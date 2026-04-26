# Clinical Trial Protocol Auditor — Project Write-up

> *The first OpenEnv environment for clinical trial regulatory compliance — a $82 billion industry where missing a single safety gap can cost lives and millions of dollars.*

**Live Environment:** [HuggingFace Space](https://huggingface.co/spaces/ida25satapathy/clinical-trial-auditor)
**Source Code:** [GitHub Repository](https://github.com/gitadi2/clinical-trial-auditor)
**Author:** Aditya Satapathy ([@gitadi2](https://github.com/gitadi2))
**Hackathon:** Meta PyTorch OpenEnv Hackathon × Scaler School of Technology, 2026

---

## The Problem

Clinical trial protocols are 50-200 page regulatory documents that must comply with ICH-GCP E6(R2) guidelines, FDA 21 CFR regulations, and EMA directives. Today, auditing a single protocol takes 40-80 hours of expert review and costs $500K to $10M+ per amendment. Approximately 30% of FDA INDs have protocol deficiencies that delay approval by 6-12 months.

A single missed statistical flaw or safety gap can result in a clinical hold, a failed Phase III trial costing hundreds of millions, or — worst case — preventable patient harm.

This environment trains AI agents to catch these issues before protocols reach regulators.

---

## Why This Matters for RL Training

Most OpenEnv environments today focus on web tasks, coding, or grid worlds. Healthcare regulatory compliance is genuinely underexplored — yet it is exactly the kind of structured judgment over long documents that RL agents need to learn.

The environment teaches LLMs three capabilities current models struggle with:

1. **Long-context cross-referencing** — detecting contradictions between sections 30+ pages apart
2. **Multi-dimensional analysis** — simultaneously evaluating statistics, ethics, safety, design
3. **Workflow execution** — knowing when to request information vs. when to flag findings

---

## Environment Design

### Three Tasks Across Difficulty Levels

| Task | Difficulty | Protocol | Issues | Max Steps |
|------|------------|----------|--------|-----------|
| Section Completeness | Easy | Phase III Oncology (NSCLC) | 5 | 10 |
| Eligibility Validation | Medium | CV Outcomes Trial | 7 | 12 |
| Full Protocol Audit | Hard | Pediatric Gene Therapy (ADA-SCID) | 10 | 15 |

22 ground-truth issues across 7 categories: missing sections, logical inconsistencies, statistical errors, safety gaps, regulatory violations, endpoint issues, and consent issues.

### Procedural Protocol Generation

Beyond the 3 fixed protocols, the environment includes a generator for infinite unique training protocols across 6 therapeutic areas (oncology, cardiology, neurology, rare disease, immunology, metabolic) and multiple phases. This prevents agent memorization and forces true generalization.

### Action Space

The agent has three actions:

| Action | What It Does | Reward |
|--------|--------------|--------|
| `identify_issue` | Flag a compliance issue | +0.15 to +0.25 (correct), -0.05 (false positive), -0.10 (duplicate) |
| `request_section` | View specific protocol section | +0.02 (exists), +0.03 (missing section discovered) |
| `submit_report` | Finalize audit | +0.0 to +0.3 (based on grade) |

### Reward Design

Five-component composable scoring (totals 1.0):

- **Recall (40%)** — fraction of ground-truth issues identified
- **Precision (25%)** — fraction of findings that are true positives
- **Severity Accuracy (15%)** — correctness of critical/major/minor classification
- **Efficiency (10%)** — steps used vs. optimal
- **Coverage Quality (10%)** — keyword match confidence

Three anti-gaming mechanisms prevent reward hacking:
- Duplicate detection (-0.10)
- False positive penalty (-0.05)
- Efficiency scoring rewards finding all issues in fewer steps

The grading is fully deterministic and keyword-based — no LLM-in-the-loop. Same input always produces the same score, which is non-negotiable for reproducible RL training.

---

## Training Results

I trained Llama-3.2-3B-Instruct using GRPO (Group Relative Policy Optimization) via HuggingFace TRL with Unsloth for 4-bit quantization.

### Reward Curves

The reward signal climbs steadily across training steps, while loss decreases:

![Training Curves](https://raw.githubusercontent.com/gitadi2/clinical-trial-auditor/main/training_curves.png)

### Before vs After

After GRPO training, the agent's score improved across all three tasks:

![Before vs After](https://raw.githubusercontent.com/gitadi2/clinical-trial-auditor/main/before_after_comparison.png)

| Task | Baseline | After Training | Improvement |
|------|----------|----------------|-------------|
| Section Completeness (Easy) | 0.100 | 0.100 | **+0.000** |
| Eligibility Validation (Medium) | 0.403 | 0.456 | **+0.053** |
| Full Protocol Audit (Hard) | 0.429 | 0.430 | **+0.001** |
| **Overall** | **0.311** | **0.329** | **+0.018%** |

The agent did not just memorize keywords — it learned the audit *workflow*. After training, it consistently performs `request_section` calls before `identify_issue` calls on uncertain sections, mirroring how a real Clinical Research Associate works.

---

## Architecture

The system has three layers:

1. **Inference Layer** — `inference.py` uses OpenAI client to call any LLM. Outputs mandatory `[START]`/`[STEP]`/`[END]` structured logs.

2. **OpenEnv Environment** — FastAPI server exposing `/reset`, `/step`, `/state`, `/grade` endpoints. Containerized with Docker, deployed on HuggingFace Spaces.

3. **Core Logic** —
   - `protocols.py` — 3 hand-crafted clinical trial protocols with planted issues
   - `protocol_generator.py` — infinite procedural protocol generation
   - `environment.py` — Episode state management, action validation, reward computation
   - `graders.py` — Deterministic keyword-matching grader producing 0.0-1.0 scores

Built with FastAPI, Pydantic v2, Docker, and OpenEnv-core. Fully containerized, deployed on HuggingFace Spaces.

---

## Why Healthcare RL is the Next Frontier

Coding benchmarks have plateaued. Web task benchmarks are saturated. The next frontier for LLM training is high-stakes professional judgment work — healthcare, legal, finance — where the cost of being wrong is enormous and the reward signal is rich.

Clinical trial regulatory compliance sits at the perfect intersection:
- High economic stakes ($82B market)
- Genuine difficulty (frontier models score 0.10-0.25 on hard tasks)
- Reproducible scoring (keyword matching, no LLM judge)
- Real-world impact (this is work CRAs and IRBs do every day)

---

## Reproducibility

- **Training notebook:** [Round2_Training_ClinicalTrialAuditor.ipynb](https://github.com/gitadi2/clinical-trial-auditor/blob/main/Round2_Training_ClinicalTrialAuditor.ipynb)
- **Open in Colab:** Available via badge in README
- **HF Space:** [ida25satapathy/clinical-trial-auditor](https://huggingface.co/spaces/ida25satapathy/clinical-trial-auditor)

All grading is deterministic. Same agent on same protocol always gives the same score.

---

## Acknowledgments

Built solo for the **Meta PyTorch OpenEnv Hackathon × Scaler School of Technology, 2026**. Selected as one of 800 finalists from 31,000+ team registrations.

Grateful to Meta, PyTorch, HuggingFace, and Scaler School of Technology for putting together a hackathon that pushes the frontier of what we can train LLMs to do.

— **Aditya Satapathy**
