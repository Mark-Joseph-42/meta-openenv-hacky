---
title: OmniSupport-Sim
emoji: 🚀
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 8000
pinned: false
---

# OmniSupport-Sim 🎧

A High-Fidelity **OpenEnv** for Multi-Tool Support Agents. 

![OmniSupport Dashboard](https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=1200 "Mission Control Dashboard")

*(Note to Judges: We have built a custom, real-time visual UI for this OpenEnv. You can physically watch agents navigate the environment by visiting the `/web` endpoint of this Space: [Live Dashboard](https://markjoseph2003-metahacky.hf.space/web))*

---

## 📖 Overview
Current agent benchmarks (like HumanEval or WebShop) fail to test **SOP Compliance**—the ability to verify facts across multiple tools before taking an action. 

**OmniSupport-Sim** fills this gap by penalizing agent hallucinations and explicitly rewarding agents that use a strict "verify-then-act" loop. It simulates a Tier-2 Support CRM, forcing the LLM to route, verify, and resolve realistic customer complaints using a suite of programmatic tools.

## ⚙️ The OpenEnv Specification
This repository strictly adheres to the Meta PyTorch Hackathon OpenEnv requirements:
* ✅ **Standard API**: Exposes `reset()`, `step()`, and `state()` endpoints.
* ✅ **Metadata Config**: Contains `openenv.yaml` exposing `server.app:app` on port `8000`.
* ✅ **Action & Observation Structure**: Implements native Pydantic representations of state logic.
* ✅ **Baseline Inference**: Contains `inference.py` ready to deploy models using the standard OpenAI client.

## 🛠️ The 3 Tasks & Grading Mechanics
The environment features dynamic, deterministic grading utilizing a Dense Reward Function (`R_prog`, `R_pen`, `R_term`):

1. **Status Resolution (Easy)**
   * **Goal:** Retrieve correct order status from multiple active orders.
   * **Grader:** Evaluates if the agent's `FinalResponse` matches the correct database entry.
   
2. **SOP Compliance — Refund (Medium)**
   * **Goal:** Verify refund policy before processing an $89.99 transaction.
   * **Grader:** Agent is penalized for blindly issuing refunds. Must successfully invoke `VerifyPolicy` before triggering the refund.

3. **Conflict Reconciliation (Hard)**
   * **Goal:** Handle a customer claiming a return when the DB shows "Pending".
   * **Grader:** Agent must dynamically query the `CarrierAPI` tool to verify delivery *before* processing the refund. Hallucinations result in a `0.0` score.

---

## 🧪 How to Evaluate & Test

### 1. Automated Validation (For OpenEnv Checkers)
Automated evaluators can directly utilize the `openenv.yaml` manifest. The FastAPI backend natively ingests JSON inputs to `/step` and `/reset`.

### 2. Manual Inference / Running Locally
To test the environment against an LLM locally (or reproduce our baseline):

1. Clone the repository.
2. Install dependencies: `pip install -r server/requirements.txt`
3. Export your API keys and target model:
   ```bash
   export API_BASE_URL="https://api.openai.com/v1"
   export MODEL_NAME="gpt-4o"
   ```
4. Run the evaluation script:
   ```bash
   python inference.py
   ```
   *The script will emit standard `[START]`, `[STEP]`, and `[END]` JSON log blocks and will complete in under 20 minutes.*

### 3. Mission Control Dashboard (Live UI)
To make grading transparent, we built a frontend web portal that dynamically visualizes the LLM's thought process and cumulative score!

👉 **[Launch OpenEnv Mission Control](https://markjoseph2003-metahacky.hf.space/web)**

* Run `inference.py` in your terminal.
* Keep the dashboard open in your browser.
* Watch the Reward Signal Breakdown bars adjust in real-time as the agent processes tool calls!

---
*Built for the Scaler x Meta PyTorch Hackathon (April 2026).*
