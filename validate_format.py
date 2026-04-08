"""Quick validation of inference.py format compliance."""
import re
import sys
import io
from contextlib import redirect_stdout

sys.path.insert(0, '.')
from inference import log_start, log_step, log_end, clamp_score, clamp_reward

lines = []
with redirect_stdout(io.StringIO()) as f:
    log_start('order_check', 'omnisupport_sim', 'Qwen/Qwen2.5-72B-Instruct')
    log_step(1, '{"action_type":"search_db","query":"cust_882"}', 0.0, False, None)
    log_step(2, '{"action_type":"final_response","text":"Delivered."}', 1.0, True, None)
    log_end(True, 2, 0.99, [0.0, 1.0])
    lines = f.getvalue().strip().split('\n')

print("=== OUTPUT LINES ===")
for i, l in enumerate(lines):
    print(f"  {i}: {repr(l)}")

start_pat = r'^\[START\] task=\S+ env=\S+ model=\S+$'
step_pat  = r'^\[STEP\] step=\d+ action=.+ reward=\d+\.\d{2} done=(true|false) error=(\S+|null)$'
end_pat   = r'^\[END\] success=(true|false) steps=\d+ score=\d+\.\d{2} rewards=[\d.,]+$'

checks = [
    ('[START] format correct',       bool(re.match(start_pat, lines[0]))),
    ('[STEP] format (step 1)',        bool(re.match(step_pat,  lines[1]))),
    ('[STEP] format (step 2)',        bool(re.match(step_pat,  lines[2]))),
    ('[END] format correct',         bool(re.match(end_pat,   lines[3]))),
    ('reward 0.0 clamped to 0.01',  clamp_reward(0.0) == 0.01),
    ('reward 1.0 clamped to 0.99',  clamp_reward(1.0) == 0.99),
    ('score 0.0 clamped to 0.01',   clamp_score(0.0)  == 0.01),
    ('score 1.0 clamped to 0.99',   clamp_score(1.0)  == 0.99),
    ('no status= in END',           'status=' not in lines[3]),
    ('no final_grade= in END',      'final_grade=' not in lines[3]),
    ('no [BONUS] in STEP',          '[BONUS]' not in lines[1]),
    ('no [PENALTY] in STEP',        '[PENALTY]' not in lines[2]),
    ('success= present in END',     'success=' in lines[3]),
    ('score= present in END',       'score=' in lines[3]),
    ('rewards= present in END',     'rewards=' in lines[3]),
]

print("\n=== FORMAT COMPLIANCE ===")
all_pass = True
for name, ok in checks:
    tag = 'PASS' if ok else 'FAIL <<<'
    if not ok:
        all_pass = False
    print(f"  [{tag}] {name}")

print()
print("ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED")
sys.exit(0 if all_pass else 1)
