"""Test the core environment logic without requiring FastAPI."""
import sys
sys.path.insert(0, "/home/claude")

# Test 1: Protocol data loads
print("=" * 60)
print("TEST 1: Protocol Data Integrity")
print("=" * 60)

from clinical_trial_auditor.server.protocols import TASKS, get_task, list_tasks

tasks = list_tasks()
assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"
print(f"  3 tasks found: {[t['id'] for t in tasks]}")

for task_id in ["section_completeness", "eligibility_validation", "full_protocol_audit"]:
    task = get_task(task_id)
    assert task["protocol_text"], f"Protocol text empty for {task_id}"
    assert len(task["ground_truth_issues"]) >= 3, f"Need 3+ issues for {task_id}"
    print(f"  {task_id}: {len(task['ground_truth_issues'])} issues, {len(task['protocol_text'])} chars")

print("PASS")

# Test 2: Grader Logic
print(f"\n{'=' * 60}")
print("TEST 2: Grader Logic")
print("=" * 60)

from clinical_trial_auditor.server.graders import grade_episode, compute_step_reward

task = get_task("section_completeness")
gt = task["ground_truth_issues"]

# Perfect findings
perfect = [{"section": i["section"], "issue_type": i["issue_type"],
            "severity": i["severity"], "description": i["description"]} for i in gt]
grade = grade_episode(perfect, gt, 6, 10)
print(f"  Perfect: score={grade['total_score']:.4f}, recall={grade['recall']}")
assert grade["total_score"] > 0.8
assert grade["recall"] == 1.0

# Empty findings
g2 = grade_episode([], gt, 1, 10)
assert g2["total_score"] == 0.0
print(f"  Empty: score={g2['total_score']}")

# Partial
partial = [perfect[0], perfect[1]]
g3 = grade_episode(partial, gt, 3, 10)
print(f"  Partial (2/{len(gt)}): score={g3['total_score']:.4f}, matched={g3['matched_count']}")
assert 0.0 < g3["total_score"] < 1.0

print("PASS")

# Test 3: Step Rewards
print(f"\n{'=' * 60}")
print("TEST 3: Step Rewards")
print("=" * 60)

r1 = compute_step_reward("identify_issue",
    {"section": "statistical_design", "issue_type": "missing_section",
     "severity": "critical", "description": "Statistical analysis plan with sample size and power is missing"},
    gt, [], 1, 10)
print(f"  Correct finding: {r1:+.4f}")
assert r1 > 0.1

r2 = compute_step_reward("identify_issue",
    {"section": "title", "issue_type": "regulatory_violation",
     "severity": "minor", "description": "Font inconsistency on page 3"},
    gt, [], 1, 10)
print(f"  False positive: {r2:+.4f}")
assert r2 < 0

r3 = compute_step_reward("request_section", None, gt, [], 1, 10)
print(f"  Section request: {r3:+.4f}")
assert r3 > 0

print("PASS")

# Test 4: Environment Lifecycle
print(f"\n{'=' * 60}")
print("TEST 4: Environment Lifecycle")
print("=" * 60)

from clinical_trial_auditor.server.environment import ClinicalTrialAuditorEnvironment

env = ClinicalTrialAuditorEnvironment()
obs = env.reset(task_id="section_completeness")
assert obs["done"] == False
assert obs["protocol_id"] == "XR-2024-001"
assert obs["step_number"] == 0
print(f"  Reset: protocol={obs['protocol_id']}")

obs2 = env.step({"action_type": "identify_issue", "section": "statistical_design",
    "issue_type": "missing_section", "severity": "critical",
    "description": "Statistical analysis plan section is completely missing. No sample size or power calculation."})
assert obs2["step_number"] == 1
assert len(obs2["identified_issues"]) == 1
print(f"  Step 1: reward={obs2['reward']:+.4f}")

obs3 = env.step({"action_type": "request_section", "section": "eligibility_criteria",
    "description": "View eligibility"})
assert obs3["step_number"] == 2
print(f"  Step 2: section request OK")

obs4 = env.step({"action_type": "submit_report", "description": "Done"})
assert obs4["done"] == True
print(f"  Submit: done={obs4['done']}")

grade = env.grade()
assert 0.0 <= grade["total_score"] <= 1.0
print(f"  Grade: {grade['total_score']:.4f}")

state = env.state
assert state["is_done"] == True
print(f"  State: steps={state['step_count']}, done={state['is_done']}")
print("PASS")

# Test 5: All three tasks
print(f"\n{'=' * 60}")
print("TEST 5: All Tasks Execute")
print("=" * 60)

for tid in ["section_completeness", "eligibility_validation", "full_protocol_audit"]:
    e = ClinicalTrialAuditorEnvironment()
    o = e.reset(task_id=tid)
    assert o["done"] == False and o["protocol_text"]
    o = e.step({"action_type": "submit_report", "description": "quick"})
    assert o["done"] == True
    g = e.grade()
    assert g["total_score"] == 0.0
    print(f"  {tid}: OK (0 findings = 0.0)")
print("PASS")

# Test 6: Score range [0, 1]
print(f"\n{'=' * 60}")
print("TEST 6: Score Range")
print("=" * 60)

for tid, task in TASKS.items():
    gt = task["ground_truth_issues"]
    for n in [0, 1, len(gt), len(gt)+5]:
        findings = []
        for i in range(min(n, len(gt))):
            findings.append({"section": gt[i]["section"], "issue_type": gt[i]["issue_type"],
                "severity": gt[i]["severity"], "description": gt[i]["description"]})
        for i in range(max(0, n - len(gt))):
            findings.append({"section": "x", "issue_type": "x", "severity": "minor",
                "description": f"False positive {i}"})
        g = grade_episode(findings, gt, n+1, task["max_steps"])
        assert 0.0 <= g["total_score"] <= 1.0
    print(f"  {tid}: all in [0.0, 1.0]")
print("PASS")

# Test 7: Max steps
print(f"\n{'=' * 60}")
print("TEST 7: Max Steps")
print("=" * 60)
e = ClinicalTrialAuditorEnvironment()
o = e.reset(task_id="section_completeness")
for i in range(12):
    if o["done"]: break
    o = e.step({"action_type": "identify_issue", "section": "x",
        "issue_type": "missing_section", "severity": "minor", "description": f"Finding {i}"})
assert o["done"] == True
print(f"  Auto-terminates at step {o['step_number']}")
print("PASS")

# Test 8: Invalid actions
print(f"\n{'=' * 60}")
print("TEST 8: Invalid Actions")
print("=" * 60)
e = ClinicalTrialAuditorEnvironment()
e.reset(task_id="section_completeness")
o = e.step({"action_type": "invalid", "description": "bad"})
assert o["last_action_error"] is not None
print(f"  Invalid type: error caught")
o = e.step({"action_type": "identify_issue", "description": ""})
assert o["last_action_error"] is not None
print(f"  Empty desc: error caught")
print("PASS")

print(f"\n{'=' * 60}")
print("ALL 8 TESTS PASSED")
print("=" * 60)
