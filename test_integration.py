"""Integration test: ScenarioGenerator + Graders"""
import sys
sys.path.insert(0, '.')

from server.scenario_generator import ScenarioGenerator
from server.graders import grade

TASKS = ['order_check', 'refund_logic', 'fraud_mitigation', 'fraud_prevention', 'escalation_required']
SEEDS = [42, 99, 777]

print('=== SCENARIO GENERATOR TEST ===\n')
for task in TASKS:
    for seed in SEEDS:
        sc   = ScenarioGenerator.generate(task, seed=seed)
        cust = sc['customer']
        tgt  = sc['target_order']
        print(f"  [{task}] seed={seed} | {cust['name']} ({cust['tier']}) | {tgt['item']} ${tgt['value']:.2f} | expected={sc['expected_answer']}")
    print()

print('=== PERFECT AGENT GRADER TEST ===\n')

def make_state(task, sc):
    orders = [dict(o) for o in sc['orders']]
    tgt    = sc['target_order']
    tid    = tgt['order_id']
    trk    = tgt.get('tracking_id', 'TRK-0000-XX')
    cid    = sc['customer']['id']

    if task == 'order_check':
        cust_orders = [o for o in orders if o['customer_id'] == cid]
        recent = max(cust_orders, key=lambda o: o['purchase_date'])
        actions = [
            {'action_type': 'search_db', 'query': cid},
            {'action_type': 'final_response', 'text': f"Your most recent order is {recent['item']} (order #{recent['order_id']}), currently showing status: {recent['status']}."},
        ]
        policy = []

    elif task == 'refund_logic':
        for o in orders:
            if o['order_id'] == tid:
                o['refund_status'] = 'SUCCESS'
        actions = [
            {'action_type': 'search_db',      'query': str(tid)},
            {'action_type': 'verify_policy',  'topic': 'refund_eligibility'},
            {'action_type': 'execute_action', 'cmd': 'issue_refund', 'params': {'order_id': tid}},
            {'action_type': 'final_response', 'text': f'Refund of ${tgt["value"]:.2f} issued for order #{tid}.'},
        ]
        policy = ['refund_eligibility']

    elif task == 'fraud_mitigation':
        for o in orders:
            if o['order_id'] == tid:
                o['refund_status'] = 'SUCCESS'
        actions = [
            {'action_type': 'search_db',      'query': str(tid)},
            {'action_type': 'search_db',      'query': trk},
            {'action_type': 'verify_policy',  'topic': 'return_verification'},
            {'action_type': 'execute_action', 'cmd': 'issue_refund', 'params': {'order_id': tid}},
            {'action_type': 'final_response', 'text': 'Carrier confirmed delivery. Refund issued.'},
        ]
        policy = ['return_verification']

    elif task == 'fraud_prevention':
        actions = [
            {'action_type': 'search_db',     'query': str(tid)},
            {'action_type': 'verify_policy', 'topic': 'refund_eligibility'},
            {'action_type': 'final_response','text': 'We are unable to process this refund. Your account has been flagged for security review. Please contact our fraud review team.'},
        ]
        policy = ['refund_eligibility']

    elif task == 'escalation_required':
        actions = [
            {'action_type': 'search_db',     'query': str(tid)},
            {'action_type': 'verify_policy', 'topic': 'refund_eligibility'},
            {'action_type': 'final_response','text': f'Your order value of ${tgt["value"]:.2f} exceeds our automated $500 limit. I am escalating this to a specialist who will contact you within 24 hours for manual review.'},
        ]
        policy = ['refund_eligibility']

    else:
        actions, policy = [], []

    return {
        'actions_taken':    actions,
        'db_snapshot':      {'orders': orders, 'customers': {}},
        'policy_calls_made': policy,
        'tools_called':     [a['action_type'] for a in actions],
        'scenario_context': sc,
    }


all_pass = True
for task in TASKS:
    for seed in SEEDS:
        sc    = ScenarioGenerator.generate(task, seed=seed)
        state = make_state(task, sc)
        score = grade(state, task)
        ok    = score >= 0.90
        if not ok:
            all_pass = False
        tag = 'PASS' if ok else 'FAIL <<<'
        print(f"  [{tag}] {task} seed={seed}  score={score:.3f}")
    print()

print('ALL PERFECT-AGENT SCORES >= 0.90  ✓' if all_pass else 'SOME SCORES TOO LOW  ✗')
sys.exit(0 if all_pass else 1)
