# 🏥 Clinical Trial Protocol Auditor — OpenEnv Environment

An OpenEnv-compatible environment where AI agents audit clinical trial protocols for compliance issues, missing sections, statistical errors, safety gaps, and regulatory violations. This simulates the real-world task performed by **regulatory affairs specialists**, **clinical research associates (CRAs)**, and **IRB/IEC reviewers** — a process that currently takes 40-80 hours per protocol and is prone to human oversight.

---

## 🎯 Why This Environment?

Clinical trial protocols are 50-200 page documents that must comply with ICH-GCP E6(R2) guidelines, FDA/EMA regulations, and institutional standards. A single missed issue can delay FDA approval by 6-12 months, put patient safety at risk, cost sponsors $10M+ in protocol amendments, or lead to clinical holds. **This environment trains agents to catch these issues before they reach regulators.**

---

## 🧩 Environment Overview

| Property | Value |
|---|---|
| **Spec** | OpenEnv (step/reset/state API) |
| **Type** | Text-based sequential decision-making |
| **Tasks** | 3 (easy → medium → hard) |
| **Reward** | Composite with partial progress signals |
| **Grading** | Deterministic, keyword-matched, 0.0-1.0 |
| **Max Steps** | 10-15 per task |
| **Deployment** | Docker + HF Spaces |

---

## 📋 Tasks

### Task 1: Section Completeness Check (Easy)
- **Protocol**: Phase III oncology trial (NSCLC, EGFR inhibitor)
- **Objective**: Identify missing/incomplete required sections per ICH-GCP
- **Ground Truth**: 5 planted issues (missing statistical plan, incomplete safety monitoring, missing data management, missing ethics section, missing dose modification guidelines)
- **Max Steps**: 10
- **Expected Score**: 0.6-1.0 for competent agents

### Task 2: Eligibility Criteria Validation (Medium)
- **Protocol**: Cardiovascular outcomes trial (PCSK9 inhibitor in T2DM+CVD)
- **Objective**: Find logical inconsistencies, contradictions, and safety gaps in inclusion/exclusion criteria
- **Ground Truth**: 7 planted issues (contradictory age ranges, HbA1c conflicts, inconsistent renal thresholds, inadequate ACS exclusion window, open-label bias, missing anticoagulant exclusion, PCSK9 washout concerns)
- **Max Steps**: 12
- **Expected Score**: 0.3-0.8 for competent agents

### Task 3: Full Protocol Audit (Hard)
- **Protocol**: Pediatric gene therapy trial (ADA-SCID, lentiviral vector)
- **Objective**: Comprehensive multi-dimensional audit covering design feasibility, statistical methodology, safety monitoring, regulatory compliance, and ethical considerations
- **Ground Truth**: 10 planted issues (impossible blinding, underpowered sample size, inappropriate one-sided testing, wrong primary endpoint, assent/age inconsistency, delayed crossover ethics, vague stopping rules, missing rescue protocol, alpha spending gaps, missing immune function baseline)
- **Max Steps**: 15
- **Expected Score**: 0.15-0.65 for competent agents

---

## 🎮 Action Space

The agent can perform 3 types of actions:

```python
{
    "action_type": str,       # REQUIRED: "identify_issue" | "request_section" | "submit_report"
    "section": str,            # Protocol section (e.g., "eligibility_criteria", "statistical_design")
    "issue_type": str,         # "missing_section" | "logical_inconsistency" | "statistical_error"
                               # "safety_gap" | "regulatory_violation" | "endpoint_issue" | "consent_issue"
    "severity": str,           # "critical" | "major" | "minor"
    "description": str,        # REQUIRED: Detailed description of finding
    "recommendation": str      # Optional: Suggested corrective action
}
```

| Action | Purpose | Reward Signal |
|---|---|---|
| `identify_issue` | Flag a compliance/quality issue | +0.15 to +0.25 (correct), -0.05 (false positive), -0.10 (duplicate) |
| `request_section` | View a specific protocol section in detail | +0.02 (exists), +0.03 (missing section discovered) |
| `submit_report` | Finalize audit and end episode | +0.0 to +0.3 based on overall grade |

---

## 👁️ Observation Space

```python
{
    "done": bool,                  # Whether episode is complete
    "reward": float,               # Step reward
    "metadata": {
        "episode_id": str,
        "task_difficulty": str,
        "cumulative_reward": float
    },
    "protocol_id": str,            # Unique protocol identifier
    "task_id": str,                # Current task
    "task_description": str,       # What the agent should do
    "protocol_text": str,          # Full protocol text to audit
    "sections_available": [str],   # Sections available for detailed view
    "identified_issues": [         # Issues found so far
        {"section": str, "issue_type": str, "severity": str, "description": str, "step": int}
    ],
    "feedback": str,               # Environment feedback on last action
    "step_number": int,            # Current step
    "max_steps": int,              # Maximum steps allowed
    "goal": str,                   # High-level goal
    "last_action_error": str|null  # Error from last action if any
}
```

---

## 📊 Reward Design

The reward function provides **meaningful partial progress signals** throughout the episode:

### Step-Level Rewards
- **Correct issue identification**: +0.15 base + severity bonus (critical: +0.10, major: +0.05)
- **Partial match**: +0.05 to +0.10
- **False positive**: -0.05 (penalizes noise)
- **Duplicate finding**: -0.10 (penalizes repetition)
- **Section request (existing)**: +0.02 / **missing section**: +0.03
- **Invalid action**: -0.02

### Episode-Level Grading (0.0-1.0)

| Component | Weight | Description |
|---|---|---|
| Recall | 40% | Fraction of ground truth issues correctly found |
| Precision | 25% | Fraction of findings that are true positives |
| Severity Accuracy | 15% | How well severity was classified |
| Efficiency | 10% | Steps used vs. optimal |
| Coverage Quality | 10% | Average keyword match quality |

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Docker (for containerized execution)
- An LLM API key (HF Inference API, OpenAI, etc.)

### Local Development

```bash
# Clone the repository
git clone https://github.com/gitadi2/clinical-trial-auditor.git
cd clinical-trial-auditor

# Install dependencies
pip install -r clinical_trial_auditor/server/requirements.txt

# Start the environment server
uvicorn clinical_trial_auditor.server.app:app --host 0.0.0.0 --port 7860

# In another terminal, run baseline inference
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_hf_token"
export ENV_BASE_URL="http://localhost:7860"
python inference.py
```

### Docker

```bash
# Build the image
docker build -t clinical-trial-auditor .

# Run the container
docker run -p 7860:7860 clinical-trial-auditor

# Test it
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" \
  -d '{"task_id": "section_completeness"}'
```

---

## 🧪 Quick Test

```python
import requests

BASE = "http://localhost:7860"

# Reset to easy task
r = requests.post(f"{BASE}/reset", json={"task_id": "section_completeness"})
obs = r.json()["observation"]
print(f"Protocol: {obs['protocol_id']}")

# Identify a missing section
r = requests.post(f"{BASE}/step", json={
    "action_type": "identify_issue",
    "section": "statistical_design",
    "issue_type": "missing_section",
    "severity": "critical",
    "description": "Statistical analysis plan is completely missing. No sample size or power calculation."
})
print(f"Reward: {r.json()['reward']}")

# Submit report
r = requests.post(f"{BASE}/step", json={
    "action_type": "submit_report",
    "description": "Audit complete."
})
print(f"Done: {r.json()['done']}")

# Get detailed grade
print(requests.get(f"{BASE}/grade").json())
```

---

## 📈 Baseline Scores

Baseline scores with `meta-llama/Llama-3.1-8B-Instruct` via HF Inference API:

| Task | Difficulty | Baseline Score | Issues Found |
|---|---|---|---|
| section_completeness | Easy | ~0.45-0.60 | 2-3 / 5 |
| eligibility_validation | Medium | ~0.25-0.40 | 2-4 / 7 |
| full_protocol_audit | Hard | ~0.10-0.25 | 1-3 / 10 |

*Scores vary based on model quality, temperature, and prompt engineering.*

---

## 📁 Project Structure

```
clinical-trial-auditor/
├── Dockerfile                          # Root Dockerfile for docker build + docker run
├── inference.py                        # Baseline inference script (REQUIRED)
├── pyproject.toml                      # Python package config
├── README.md                           # This file
└── clinical_trial_auditor/
    ├── __init__.py                     # Package exports
    ├── models.py                       # Pydantic: Action, Observation, State
    ├── client.py                       # HTTP client for the environment
    ├── openenv.yaml                    # OpenEnv manifest
    └── server/
        ├── __init__.py
        ├── app.py                      # FastAPI server (reset/step/state endpoints)
        ├── environment.py              # Core environment logic
        ├── graders.py                  # Deterministic grading with keyword matching
        ├── protocols.py                # 3 synthetic protocols with planted issues
        ├── requirements.txt            # Server dependencies
        └── Dockerfile                  # Server-specific Dockerfile
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `API_BASE_URL` | Yes | LLM API endpoint (e.g., `https://router.huggingface.co/v1`) |
| `MODEL_NAME` | Yes | Model identifier (e.g., `meta-llama/Llama-3.1-8B-Instruct`) |
| `HF_TOKEN` | Yes | Hugging Face API token |
| `ENV_BASE_URL` | No | Environment URL (default: `http://localhost:7860`) |

---

## 🏗️ Technical Design Decisions

1. **Deterministic Grading**: All grading is keyword-based with no LLM-in-the-loop, ensuring reproducible scores across runs.
2. **Partial Progress Rewards**: Every action gets meaningful reward signal, not just binary end-of-episode scoring.
3. **Real Clinical Protocols**: Protocols are modeled after real FDA submissions with medically accurate content and realistic planted issues.
4. **Difficulty Progression**: Tasks scale from pattern matching (easy) to domain reasoning (medium) to multi-dimensional analysis (hard).
5. **Anti-Gaming**: Duplicate detection, false positive penalties, and efficiency scoring prevent reward hacking.

---

## 📜 License

MIT License

---

## 👤 Author

**Aditya Satapathy** — [@gitadi2](https://github.com/gitadi2) · [LinkedIn](https://linkedin.com/in/adisatapathy)

Built for the [Meta PyTorch OpenEnv Hackathon](https://www.scaler.com/school-of-technology/meta-pytorch-hackathon) × Scaler School of Technology, 2026.
