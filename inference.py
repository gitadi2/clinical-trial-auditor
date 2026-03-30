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
"""

import os
import re
import json
import textwrap
import time
from typing import List, Optional, Dict, Any

import requests
from openai import OpenAI

# ── Environment Configuration ───────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or ""
MODEL_NAME = os.getenv("MODEL_NAME") or "meta-llama/Llama-3.1-8B-Instruct"

# Environment URL — update to your HF Space URL after deployment
ENV_BASE_URL = os.getenv("ENV_BASE_URL") or "http://localhost:7860"

MAX_STEPS = 10
TEMPERATURE = 0.2
MAX_TOKENS = 1024

DEBUG = True

# ── Task Definitions ─────────────────────────────────────────────────────────

TASKS = [
    "section_completeness",      # Easy
    "eligibility_validation",    # Medium
    "full_protocol_audit",       # Hard
]

# ── System Prompt ─────────────────────────────────────────────────────────────

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

    Strategy:
    1. Read the protocol text carefully
    2. Identify issues one at a time using "identify_issue" actions
    3. Use "request_section" if you need to see a specific section in more detail
    4. When you've found all issues, use "submit_report" to finalize

    Focus on:
    - Missing or incomplete required sections (per ICH-GCP)
    - Logical inconsistencies in eligibility criteria
    - Statistical design flaws (sample size, power, endpoints)
    - Safety monitoring gaps
    - Regulatory compliance issues
    - Cross-section consistency problems
""").strip()


# ── Helper Functions ──────────────────────────────────────────────────────────

def env_reset(task_id: str) -> Dict[str, Any]:
    """Reset the environment for a given task."""
    resp = requests.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_id": task_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_step(action: Dict[str, Any]) -> Dict[str, Any]:
    """Take a step in the environment."""
    resp = requests.post(
        f"{ENV_BASE_URL}/step",
        json=action,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def env_grade() -> Dict[str, Any]:
    """Get the grade for the current episode."""
    resp = requests.get(f"{ENV_BASE_URL}/grade", timeout=30)
    resp.raise_for_status()
    return resp.json()


def build_user_prompt(step: int, observation: Dict[str, Any], history: List[str]) -> str:
    """Build the user prompt from the current observation."""
    obs = observation.get("observation", observation)
    task_desc = obs.get("task_description", "")
    protocol_text = obs.get("protocol_text", "")
    feedback = obs.get("feedback", "")
    identified = obs.get("identified_issues", [])
    step_num = obs.get("step_number", step)
    max_steps = obs.get("max_steps", MAX_STEPS)

    # Truncate protocol text if too long (keep first and last parts)
    if len(protocol_text) > 6000:
        half = 2800
        protocol_text = protocol_text[:half] + "\n\n[... protocol text truncated ...]\n\n" + protocol_text[-half:]

    issues_str = ""
    if identified:
        issues_str = "\nIssues identified so far:\n"
        for i, iss in enumerate(identified, 1):
            issues_str += (
                f"  {i}. [{iss.get('severity', '?')}] {iss.get('section', '?')}: "
                f"{iss.get('description', '?')[:100]}...\n"
            )

    history_str = "\n".join(history[-4:]) if history else "None"

    prompt = textwrap.dedent(f"""
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

    return prompt


def parse_model_action(response_text: str) -> Dict[str, Any]:
    """Parse the model's response into an action dict."""
    if not response_text:
        return {
            "action_type": "submit_report",
            "description": "No response from model, submitting report.",
        }

    # Try to extract JSON from the response
    text = response_text.strip()

    # Remove markdown code fences if present
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    # Try to find JSON object in the text
    json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
    if json_match:
        try:
            action = json.loads(json_match.group())
            # Validate required fields
            if "action_type" not in action:
                action["action_type"] = "identify_issue"
            if "description" not in action:
                action["description"] = text[:200]
            return action
        except json.JSONDecodeError:
            pass

    # Fallback: try to parse the entire text as JSON
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

    # Last resort: wrap the text as a finding description
    return {
        "action_type": "identify_issue",
        "description": text[:500],
        "severity": "major",
        "section": "general",
        "issue_type": "regulatory_violation",
    }


# ── Main Inference Loop ──────────────────────────────────────────────────────

def run_task(client: OpenAI, task_id: str) -> Dict[str, Any]:
    """Run inference on a single task and return the grade."""
    print(f"\n{'='*60}")
    print(f"TASK: {task_id}")
    print(f"{'='*60}")

    # Reset environment
    reset_result = env_reset(task_id)
    observation = reset_result.get("observation", reset_result)

    print(f"Protocol: {observation.get('protocol_id', '?')}")
    print(f"Task: {observation.get('task_description', '?')[:100]}...")
    print(f"Max steps: {observation.get('max_steps', MAX_STEPS)}")

    history: List[str] = []
    done = reset_result.get("done", False)
    total_reward = 0.0

    for step in range(1, MAX_STEPS + 1):
        if done:
            print("Episode done. Stopping early.")
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
        except Exception as exc:  # noqa: BLE001
            print(f"  LLM error at step {step}: {exc}")
            response_text = '{"action_type": "submit_report", "description": "LLM error, submitting."}'

        # Parse action
        action = parse_model_action(response_text)

        if DEBUG:
            print(f"\n  Step {step}: {action.get('action_type', '?')}")
            desc = action.get('description', '')[:80]
            print(f"    Description: {desc}...")

        # Execute step
        result = env_step(action)
        observation = result.get("observation", result)
        reward = result.get("reward", 0.0)
        done = result.get("done", False)
        total_reward += reward

        # Record history
        action_str = action.get("action_type", "?")
        history_line = f"Step {step}: {action_str} -> reward {reward:+.2f}"
        history.append(history_line)

        if DEBUG:
            feedback = observation.get("feedback", "")[:100]
            print(f"    Reward: {reward:+.4f} | Done: {done}")
            print(f"    Feedback: {feedback}")

        if done:
            print("Episode complete.")
            break
    else:
        print(f"Reached max steps ({MAX_STEPS}).")

    # Get final grade
    grade = env_grade()
    print(f"\n  FINAL SCORE: {grade.get('total_score', 0.0):.4f}")
    print(f"  Recall: {grade.get('recall', 0):.3f} | Precision: {grade.get('precision', 0):.3f}")
    print(f"  Matched: {grade.get('matched_count', 0)}/{grade.get('total_ground_truth', 0)}")
    print(f"  Total Reward: {total_reward:+.4f}")

    return grade


def main() -> None:
    """Run baseline inference on all 3 tasks."""
    print("=" * 60)
    print("Clinical Trial Protocol Auditor — Baseline Inference")
    print("=" * 60)
    print(f"API_BASE_URL: {API_BASE_URL}")
    print(f"MODEL_NAME:   {MODEL_NAME}")
    print(f"ENV_BASE_URL: {ENV_BASE_URL}")
    print()

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    results = {}
    for task_id in TASKS:
        try:
            grade = run_task(client, task_id)
            results[task_id] = grade
        except Exception as exc:
            print(f"\nERROR on task {task_id}: {exc}")
            results[task_id] = {"total_score": 0.0, "error": str(exc)}

    # Print summary
    print("\n" + "=" * 60)
    print("BASELINE RESULTS SUMMARY")
    print("=" * 60)
    for task_id, grade in results.items():
        score = grade.get("total_score", 0.0)
        difficulty = {"section_completeness": "easy", "eligibility_validation": "medium", "full_protocol_audit": "hard"}
        diff = difficulty.get(task_id, "?")
        print(f"  {task_id} ({diff}): {score:.4f}")

    avg = sum(g.get("total_score", 0.0) for g in results.values()) / len(results)
    print(f"\n  AVERAGE SCORE: {avg:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
