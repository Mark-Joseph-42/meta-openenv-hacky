"""Verify the actual inference.py output format from the live run."""
import re

output = (
    "[START] task=order_check env=omnisupport_sim model=gpt-4o-mini\n"
    "[STEP] step=1 action={\"action_type\": \"final_response\", \"text\": \"Model error.\"} reward=0.01 done=true error=null\n"
    "[END] success=false steps=1 score=0.01 rewards=0.01\n"
    "[START] task=refund_logic env=omnisupport_sim model=gpt-4o-mini\n"
    "[STEP] step=1 action={\"action_type\": \"final_response\", \"text\": \"Model error.\"} reward=0.01 done=true error=null\n"
    "[END] success=false steps=1 score=0.01 rewards=0.01\n"
    "[START] task=fraud_mitigation env=omnisupport_sim model=gpt-4o-mini\n"
    "[STEP] step=1 action={\"action_type\": \"final_response\", \"text\": \"Model error.\"} reward=0.01 done=true error=null\n"
    "[END] success=false steps=1 score=0.01 rewards=0.01"
)

lines = output.strip().split('\n')
start_lines = [l for l in lines if l.startswith('[START]')]
step_lines  = [l for l in lines if l.startswith('[STEP]')]
end_lines   = [l for l in lines if l.startswith('[END]')]

start_pat = r'^\[START\] task=\S+ env=\S+ model=\S+$'
step_pat  = r'^\[STEP\] step=\d+ action=.+ reward=\d+\.\d{2} done=(true|false) error=(\S+|null)$'
end_pat   = r'^\[END\] success=(true|false) steps=\d+ score=\d+\.\d{2} rewards=[\d.,]+$'

reward_vals = [float(m.group(1)) for l in step_lines for m in [re.search(r'reward=(\d+\.\d+)', l)] if m]
score_vals  = [float(m.group(1)) for l in end_lines  for m in [re.search(r'score=(\d+\.\d+)', l)]  if m]

checks = [
    ('3x [START] lines emitted',     len(start_lines) == 3),
    ('3x [END] lines emitted',       len(end_lines)   == 3),
    ('All [START] format valid',     all(re.match(start_pat, l) for l in start_lines)),
    ('All [STEP] format valid',      all(re.match(step_pat,  l) for l in step_lines)),
    ('All [END] format valid',       all(re.match(end_pat,   l) for l in end_lines)),
    ('All rewards strictly in (0,1)',all(0.0 < r < 1.0 for r in reward_vals)),
    ('All scores strictly in (0,1)', all(0.0 < s < 1.0 for s in score_vals)),
    ('No status= in any END line',   all('status=' not in l for l in end_lines)),
    ('No final_grade= in END',       all('final_grade=' not in l for l in end_lines)),
    ('No [BONUS]/[PENALTY] tags',    all('[BONUS]' not in l and '[PENALTY]' not in l for l in step_lines)),
    ('success= field present',       all('success=' in l for l in end_lines)),
    ('score= field present',         all('score=' in l for l in end_lines)),
    ('rewards= field present',       all('rewards=' in l for l in end_lines)),
]

print("=== EVALUATOR COMPLIANCE CHECK ===\n")
all_pass = True
for name, ok in checks:
    tag = 'PASS' if ok else 'FAIL <<<'
    if not ok:
        all_pass = False
    print(f"  [{tag}] {name}")

print(f"\nReward values found: {reward_vals}")
print(f"Score values found:  {score_vals}")
print()
if all_pass:
    print("ALL CHECKS PASSED — ready to submit!")
else:
    print("SOME CHECKS FAILED — fix before submitting!")
    import sys; sys.exit(1)
