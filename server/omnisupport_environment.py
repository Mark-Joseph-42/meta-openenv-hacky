"""
OmniSupport-Sim Environment — Core implementation.
Implements the OpenEnv spec: reset(), step(), state()

Upgraded: uses ScenarioGenerator for fully dynamic, seed-reproducible episodes.
"""
import uuid
import random
from typing import Optional

from omnisupport_sim.models import (
    OmniSupportObservation,
    OmniSupportState,
)
from server.mock_db import MockDB
from server.policy_kb import lookup_policy
from server.carrier_api import query_carrier
from server.reward import RewardCalculator
from server.graders import grade
from server.scenario_generator import ScenarioGenerator

SUPPORTED_TASKS = [
    "order_check",
    "refund_logic",
    "fraud_mitigation",
    "fraud_prevention",
    "escalation_required",
]


class OmniSupportEnvironment:
    """OpenEnv-compliant environment for Tier-2 Support Simulation.

    Each reset() call generates a fresh, seed-reproducible scenario via
    ScenarioGenerator, covering 5 distinct task types with randomized
    customers, order values, dates, fraud flags, and carrier data.
    """

    def __init__(self):
        self.db = MockDB()
        self.reward_calc = RewardCalculator()
        self._state: Optional[OmniSupportState] = None
        self._current_scenario: Optional[dict] = None

    def reset(self, task_id: str = "order_check", seed: Optional[int] = None) -> dict:
        """Initialize a new episode with a dynamically generated scenario.

        Args:
            task_id: One of the 5 supported task IDs, or 'random'
            seed: Optional int for reproducible scenario generation

        Returns:
            Initial observation dict
        """
        self.db.reset()
        self.reward_calc.reset()

        # ── Resolve task_id ──
        if task_id == "random":
            task_id = random.choice(SUPPORTED_TASKS)

        if task_id not in SUPPORTED_TASKS:
            raise ValueError(f"Unknown task_id: '{task_id}'. Valid: {SUPPORTED_TASKS}")

        # ── Generate dynamic scenario ──
        episode_seed = seed if seed is not None else random.randint(0, 2**31)
        scenario = ScenarioGenerator.generate(task_id, seed=episode_seed)

        # ── Populate MockDB from scenario ──
        self.db.load_scenario(scenario)
        self._current_scenario = scenario
        self._current_scenario["_seed"] = episode_seed

        customer_id      = scenario["customer"]["id"]
        customer_history = self.db.get_customer_history(customer_id)

        self._state = OmniSupportState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            current_task_id=task_id,
            db_snapshot=self.db.get_snapshot(),
            policy_calls_made=[],
            actions_taken=[],
            tools_called=[],
            reward_accumulated=0.0,
            done=False,
        )

        observation = OmniSupportObservation(
            ticket_id=scenario["ticket_id"],
            customer_history=customer_history,
            internal_notes=f"New ticket: {scenario['ticket_text']}",
            last_tool_output=None,
        )

        return {
            "observation": observation.model_dump(),
            "reward":      0.0,
            "done":        False,
            "info": {
                "task_id":     task_id,
                "description": scenario["description"],
                "seed":        episode_seed,
            },
        }

    def step(self, action: dict) -> dict:
        """Process an agent action.

        Args:
            action: Dict with action_type and relevant fields

        Returns:
            Observation, reward, done, info dict
        """
        if self._state is None:
            raise RuntimeError("Must call reset() before step()")
        if self._state.done:
            if action.get("action_type") == "final_response":
                # Idempotent: already closed
                customer_id = self._current_scenario["customer"]["id"]
                obs = OmniSupportObservation(
                    ticket_id=self._current_scenario["ticket_id"],
                    customer_history=self.db.get_customer_history(customer_id),
                    internal_notes="Ticket already resolved.",
                    last_tool_output={"response_sent": True, "already_done": True},
                )
                return {
                    "observation": obs.model_dump(),
                    "reward": 0.0,
                    "done": True,
                    "info": {"status": "already_done"},
                }
            raise RuntimeError("Episode is done. Call reset() to start a new one.")

        action_type    = action.get("action_type")
        tool_output    = None
        internal_notes = ""
        done           = False

        # ── Route action ──────────────────────────────────────────────────────
        if action_type == "search_db":
            query = action.get("query", "")
            # If query looks like a tracking ID → route to CarrierAPI (hidden state design)
            if "TRK-" in query.upper():
                tool_output = query_carrier(query.strip(), self._current_scenario.get("carrier_data", {}))
                self.reward_calc.carrier_queried = True
                internal_notes = f"CarrierAPI('{query}') — shipment data retrieved"
            else:
                result = self.db.search_orders(query)
                tool_output = {"results": result, "count": len(result)} if isinstance(result, list) else result
                # Auto-detect if result contains a tracking_id the agent should follow up on
                if isinstance(result, list) and result:
                    trks = [o.get("tracking_id") for o in result if o.get("tracking_id")]
                    if trks:
                        internal_notes = f"SearchDB('{query}') — {len(result)} orders found. Tracking IDs available: {', '.join(trks)}"
                    else:
                        internal_notes = f"SearchDB('{query}') — {len(result)} results found"
                else:
                    internal_notes = f"SearchDB('{query}') — no results found"

        elif action_type == "verify_policy":
            topic = action.get("topic", "")
            tool_output = lookup_policy(topic)
            self._state.policy_calls_made.append(topic)
            self.reward_calc.policy_verified = True
            internal_notes = f"VerifyPolicy('{topic}') — policy retrieved"

        elif action_type == "execute_action":
            cmd    = action.get("cmd", "")
            params = action.get("params", {})
            if cmd == "issue_refund":
                order_id = params.get("order_id")
                if order_id:
                    tool_output = self.db.update_refund_status(int(order_id), "SUCCESS")
                else:
                    tool_output = {"error": "Missing order_id parameter"}
                internal_notes = f"ExecuteAction('{cmd}') — processed"
            else:
                tool_output    = {"error": f"Unknown command: {cmd}"}
                internal_notes = f"ExecuteAction('{cmd}') — unknown command"

        elif action_type == "final_response":
            text           = action.get("text", "")
            tool_output    = {"response_sent": True, "text": text}
            internal_notes = "FinalResponse sent to customer"
            done           = True

        else:
            tool_output    = {"error": f"Unknown action_type: {action_type}"}
            internal_notes = f"Unknown action_type: {action_type}"

        # ── Record action ──────────────────────────────────────────────────────
        self._state.actions_taken.append(action)
        self._state.tools_called.append(action_type)
        self._state.step_count += 1

        # ── Compute reward ─────────────────────────────────────────────────────
        step_reward = self.reward_calc.compute_step_reward(
            action,
            tool_output if isinstance(tool_output, dict) else {"results": tool_output},
        )

        # ── Terminal reward ────────────────────────────────────────────────────
        if done:
            self._state.db_snapshot = self.db.get_snapshot()
            # Inject scenario context for dynamic graders
            state_dict = self._state.model_dump()
            state_dict["scenario_context"] = self._current_scenario
            grader_score = grade(state_dict, self._state.current_task_id)
            self._state.grader_score = grader_score
            terminal_reward = self.reward_calc.compute_terminal_reward(grader_score)
            step_reward = terminal_reward   # Replace step reward with terminal reward

        self._state.reward_accumulated += step_reward
        self._state.done = done
        self._state.db_snapshot = self.db.get_snapshot()

        # ── Build observation ──────────────────────────────────────────────────
        customer_id      = self._current_scenario["customer"]["id"]
        customer_history = self.db.get_customer_history(customer_id)
        observation = OmniSupportObservation(
            ticket_id=self._current_scenario["ticket_id"],
            customer_history=customer_history,
            internal_notes=internal_notes,
            last_tool_output=tool_output if isinstance(tool_output, dict) else {"results": tool_output},
            grader_score=self._state.grader_score if done else 0.0,
        )

        return {
            "observation": observation.model_dump(),
            "reward":      step_reward,
            "done":        done,
            "info": {
                "step_count":   self._state.step_count,
                "total_reward": self._state.reward_accumulated,
                "grader_score": self._state.grader_score,
                "sop_violations": self.reward_calc.sop_violations,
            },
        }

    def state(self) -> dict:
        """Return full state snapshot for grading and debugging."""
        if self._state is None:
            return {"error": "No active episode. Call reset() first."}
        self._state.db_snapshot = self.db.get_snapshot()
        s = self._state.model_dump()
        s["scenario_context"] = self._current_scenario
        return s