"""
Inference Script — Clinical Trial Protocol Auditor
====================================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL    The API endpoint for the LLM.
    MODEL_NAME      The model identifier to use for inference.
    HF_TOKEN        Your Hugging Face / API key.

- The inference script must be named `inference.py` and placed in the root directory of the project
- Participants must use OpenAI Client for all LLM calls using above variables

STDOUT FORMAT
The script must emit exactly three line types to stdout, in this order:

[START] task=<task_name> env=<benchmark> model=<model_name>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import json
import os
import re
import textwrap
from typing import Any, Dict, List, Optional

import requests
from openai import OpenAI

# ── Environment Configuration ───────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or ""
MODEL_NAME = os.getenv("MODEL_NAME") or "meta-llama/Llama-3.1-8B-Instruct"
ENV_BASE_URL = os.getenv("ENV_BASE_URL") or "http://localhost:7860"

BENCHMARK = "clinical_trial_auditor"
MAX_STEPS = 15
TEMPERATURE = 0.2
MAX_TOKENS = 1024
SUCCESS_SCORE_THRESHOLD = 0.1

TASKS = [
    "section_completeness",
    "eligibility_validation",
    "full_protocol_audit",
]

# ── Structured Logging (MANDATORY FORMAT) ─────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ── System Prompt ─────────────────────────────────────────────────────────

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert clinical trial protocol auditor. You review clinical trial
    protocols for compliance with ICH-GCP E6(R2) guidelines, FDA/EMA regulations,
    and general best practices in clinical research.

    You interact with an audit environment using JSON actions. Each action must be
    a valid JSON object with these fields:
    - action_type: one of "identify_issue", "request_section", or "submit_report"
    - section: the protocol section name (e.g., "statistical_design", "eligibility_criteria")
    - issue_type: category of issue (e.g., "missing_section", "logical_inconsistency",
      "statistical_error", "safety_gap", "regulatory_violation", "endpoint_issue", "consent_issue")
    - severity: one of "critical", "major", "minor"
    - description: detailed description of the finding
    - recommendation: suggested fix (optional)

    RESPOND WITH ONLY A VALID JSON OBJECT. No explanations, no markdown, no extra text.

    CRITICAL RULES:
    1. NEVER repeat a finding you already made. Check the "Issues identified so far" list carefully.
       If you already flagged something about a topic, move on to a DIFFERENT issue.
    2. Look for DIFFERENT types of issues: missing sections, statistical flaws, logical
       contradictions, safety gaps, regulatory violations, endpoint problems, consent issues.
    3. Each finding must be about a DISTINCT problem. Vary the section and issue_type.
    4. After finding 3-5 unique issues, use "request_section" to look for more problems
       in specific sections you haven't examined yet.
    5. When you have found all issues you can identify, use "submit_report" to finalize.
       Do NOT keep submitting weak or repeated findings.

    Strategy:
    1. Read the protocol text carefully
    2. Identify the MOST CRITICAL issues first (missing sections, statistical errors)
    3. Then look for logical inconsistencies and safety gaps
    4. Use "request_section" to examine specific sections in detail
    5. When you've found all unique issues, use "submit_report"
""").strip()


# ── Environment API Helpers ───────────────────────────────────────────────

def env_reset(task_id: str) -> Dict[str, Any]:
    resp = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_id": task_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_step(action: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(
        f"{ENV_BASE_URL}/step",
        json=action,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_grade() -> Dict[str, Any]:
    resp = requests.get(f"{ENV_BASE_URL}/grade", timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── Prompt Builder ────────────────────────────────────────────────────────

def build_user_prompt(step: int, observation: Dict[str, Any], history: List[str]) -> str:
    obs = observation.get("observation", observation)
    task_desc = obs.get("task_description", "")
    protocol_text = obs.get("protocol_text", "")
    feedback = obs.get("feedback", "")
    identified = obs.get("identified_issues", [])
    step_num = obs.get("step_number", step)
    max_steps = obs.get("max_steps", MAX_STEPS)

    if len(protocol_text) > 6000:
        half = 2800
        protocol_text = protocol_text[:half] + "\n\n[... truncated ...]\n\n" + protocol_text[-half:]

    issues_str = ""
    if identified:
        issues_str = "\n⚠️ ISSUES ALREADY IDENTIFIED (DO NOT REPEAT THESE):\n"
        for i, iss in enumerate(identified, 1):
            issues_str += (
                f"  {i}. [{iss.get('severity', '?')}] Section: {iss.get('section', '?')} | "
                f"Type: {iss.get('issue_type', '?')} | "
                f"{iss.get('description', '?')[:150]}\n"
            )
        issues_str += "\n👉 Your next finding MUST be about a DIFFERENT section or issue type than the above.\n"

    history_str = "\n".join(history[-4:]) if history else "None"

    return textwrap.dedent(f"""
        Step: {step_num}/{max_steps}
        Task: {task_desc[:500]}

        Protocol Text:
        {protocol_text}

        {issues_str}

        Last feedback: {feedback}
        Previous actions: {history_str}

        Respond with a JSON action object. If you have found all issues, use action_type "submit_report".
        JSON action:
    """).strip()


# ── Action Parser ─────────────────────────────────────────────────────────

def parse_model_action(response_text: str) -> Dict[str, Any]:
    if not response_text:
        return {"action_type": "submit_report", "description": "No response, submitting."}

    text = response_text.strip()
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if json_match:
        try:
            action = json.loads(json_match.group())
            if "action_type" not in action:
                action["action_type"] = "identify_issue"
            if "description" not in action:
                action["description"] = text[:200]
            return action
        except json.JSONDecodeError:
            pass

    try:
        action = json.loads(text)
        if isinstance(action, dict):
            if "action_type" not in action:
                action["action_type"] = "identify_issue"
            if "description" not in action:
                action["description"] = text[:200]
            return action
    except json.JSONDecodeError:
        pass

    return {
        "action_type": "identify_issue",
        "description": text[:500],
        "severity": "major",
        "section": "general",
        "issue_type": "regulatory_violation",
    }


def action_to_short_string(action: Dict[str, Any]) -> str:
    """Convert action dict to a short string for [STEP] log."""
    atype = action.get("action_type", "unknown")
    if atype == "identify_issue":
        section = action.get("section", "general")
        desc = action.get("description", "")[:60].replace("\n", " ")
        return f"identify_issue({section}:{desc})"
    elif atype == "request_section":
        section = action.get("section", "unknown")
        return f"request_section({section})"
    elif atype == "submit_report":
        return "submit_report()"
    else:
        return f"{atype}()"


# ── Main Inference Loop ──────────────────────────────────────────────────

def run_task(client: OpenAI, task_id: str) -> Dict[str, Any]:
    """Run inference on a single task with mandatory [START]/[STEP]/[END] logging."""

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    # [START] log
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    try:
        # Reset environment
        reset_result = env_reset(task_id)
        observation = reset_result.get("observation", reset_result)

        history: List[str] = []
        done = reset_result.get("done", False)

        for step in range(1, MAX_STEPS + 1):
            if done:
                break

            # Build prompt
            user_prompt = build_user_prompt(step, {"observation": observation}, history)
            user_content = [{"type": "text", "text": user_prompt}]

            messages = [
                {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": user_content},
            ]

            # Call LLM
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    stream=False,
                )
                response_text = completion.choices[0].message.content or ""
            except Exception as exc:
                print(f"[DEBUG] LLM error at step {step}: {exc}", flush=True)
                response_text = '{"action_type": "submit_report", "description": "LLM error, submitting."}'

            # Parse action
            action = parse_model_action(response_text)
            action_str = action_to_short_string(action)

            # Execute step in environment
            result = env_step(action)
            observation = result.get("observation", result)
            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            error = observation.get("last_action_error", None)

            rewards.append(reward)
            steps_taken = step

            # [STEP] log (MANDATORY)
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            # History for context
            history.append(f"Step {step}: {action_str} -> reward {reward:+.2f}")

            if done:
                break

        # Get final grade
        grade = env_grade()
        score = grade.get("total_score", 0.0)
        score = min(max(score, 0.0), 1.0)  # clamp to [0, 1]
        success = score >= SUCCESS_SCORE_THRESHOLD

    except Exception as exc:
        print(f"[DEBUG] Task {task_id} error: {exc}", flush=True)
        score = 0.0
        success = False

    # [END] log (MANDATORY — always emitted, even on exception)
    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return {"task_id": task_id, "score": score, "steps": steps_taken, "success": success}


def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    results = {}
    for task_id in TASKS:
        results[task_id] = run_task(client, task_id)

    # Summary (not part of mandatory format, but useful for debugging)
    print("", flush=True)
    for task_id, res in results.items():
        print(f"[SUMMARY] {task_id}: score={res['score']:.2f} steps={res['steps']} success={res['success']}", flush=True)


if __name__ == "__main__":
    main()