# Copyright (c) 2026 Aditya Satapathy
# Clinical Trial Protocol Auditor - Grading Logic
# Deterministic graders that score agent performance on 0.0-1.0 scale

import re
from typing import Any, Dict, List, Tuple


def _normalize(text: str) -> str:
    """Normalize text for fuzzy matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def _keyword_match_score(finding_text: str, ground_truth: Dict[str, Any]) -> float:
    """Score how well a finding matches a ground truth issue based on keywords.

    Returns a score between 0.0 and 1.0 indicating match confidence.
    """
    normalized = _normalize(finding_text)
    keywords = ground_truth.get("keywords", [])
    if not keywords:
        return 0.0

    matched = sum(1 for kw in keywords if kw.lower() in normalized)
    # Require at least 2 keyword matches for a valid match, or 1 if there are few keywords
    min_required = min(2, len(keywords))
    if matched < min_required:
        return 0.0
    return matched / len(keywords)


def _section_match(finding_section: str, truth_section: str) -> bool:
    """Check if finding section matches ground truth section (fuzzy)."""
    if not finding_section or not truth_section:
        return True  # Don't penalize if section not specified
    f = _normalize(finding_section)
    t = _normalize(truth_section)
    # Direct match or substring
    return t in f or f in t or any(
        word in f for word in t.split("_")
    )


def _severity_score(finding_severity: str, truth_severity: str) -> float:
    """Score severity assessment accuracy."""
    severity_map = {"critical": 3, "major": 2, "minor": 1}
    f = severity_map.get(_normalize(finding_severity), 0)
    t = severity_map.get(_normalize(truth_severity), 0)
    if f == 0 or t == 0:
        return 0.5  # Unknown severity, partial credit
    diff = abs(f - t)
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.5
    else:
        return 0.0


def match_findings_to_ground_truth(
    findings: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """Match agent findings to ground truth issues using keyword matching.

    Returns:
        - matched_pairs: list of {finding, truth, match_score, severity_score}
        - unmatched_truths: IDs of ground truth issues not found
        - false_positives: descriptions of findings that don't match any truth
    """
    matched_pairs = []
    used_truths = set()
    false_positive_findings = []

    for finding in findings:
        finding_text = " ".join([
            str(finding.get("description", "")),
            str(finding.get("section", "")),
            str(finding.get("issue_type", "")),
            str(finding.get("recommendation", "")),
        ])

        best_match = None
        best_score = 0.0

        for truth in ground_truth:
            if truth["id"] in used_truths:
                continue

            score = _keyword_match_score(finding_text, truth)

            # Boost score if section matches
            if _section_match(finding.get("section", ""), truth.get("section", "")):
                score *= 1.2

            # Boost score if issue type matches
            if finding.get("issue_type") and truth.get("issue_type"):
                if _normalize(finding["issue_type"]) == _normalize(truth["issue_type"]):
                    score *= 1.1

            score = min(score, 1.0)

            if score > best_score and score >= 0.3:  # Minimum threshold
                best_score = score
                best_match = truth

        if best_match:
            used_truths.add(best_match["id"])
            sev_score = _severity_score(
                finding.get("severity", ""),
                best_match.get("severity", ""),
            )
            matched_pairs.append({
                "finding": finding,
                "truth": best_match,
                "match_score": best_score,
                "severity_score": sev_score,
            })
        else:
            false_positive_findings.append(finding.get("description", "Unknown finding"))

    unmatched_truths = [
        t["id"] for t in ground_truth if t["id"] not in used_truths
    ]

    return matched_pairs, unmatched_truths, false_positive_findings


def grade_episode(
    findings: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    steps_taken: int,
    max_steps: int,
) -> Dict[str, Any]:
    """Grade a complete episode and return detailed scoring breakdown.

    Scoring Components (all normalized to 0.0-1.0):
    - Recall (40%): Fraction of ground truth issues found
    - Precision (25%): Fraction of findings that match real issues
    - Severity Accuracy (15%): How well severity was assessed for matched findings
    - Efficiency (10%): Steps used vs needed (reward finishing in fewer steps)
    - Coverage Quality (10%): Average match quality of matched findings

    Returns dict with total_score (0.0-1.0) and component breakdown.
    """
    if not ground_truth:
        return {
            "total_score": 0.0,
            "recall": 0.0,
            "precision": 0.0,
            "severity_accuracy": 0.0,
            "efficiency": 0.0,
            "coverage_quality": 0.0,
            "details": "No ground truth issues defined.",
        }

    matched_pairs, unmatched_truths, false_positives = match_findings_to_ground_truth(
        findings, ground_truth
    )

    total_truth = len(ground_truth)
    total_findings = len(findings)

    # 1. Recall: fraction of ground truth issues found
    recall = len(matched_pairs) / total_truth if total_truth > 0 else 0.0

    # 2. Precision: fraction of findings that are true positives
    precision = len(matched_pairs) / total_findings if total_findings > 0 else 0.0

    # 3. Severity accuracy: average severity score across matches
    if matched_pairs:
        severity_accuracy = sum(m["severity_score"] for m in matched_pairs) / len(matched_pairs)
    else:
        severity_accuracy = 0.0

    # 4. Efficiency: reward using fewer steps
    if steps_taken <= 0:
        efficiency = 0.0
    elif total_findings == 0:
        efficiency = 0.0
    else:
        # Optimal steps ≈ number of ground truth issues + 1 (for submit)
        optimal_steps = total_truth + 1
        efficiency = min(1.0, optimal_steps / max(steps_taken, 1))

    # 5. Coverage quality: average match quality
    if matched_pairs:
        coverage_quality = sum(m["match_score"] for m in matched_pairs) / len(matched_pairs)
    else:
        coverage_quality = 0.0

    # Weighted total score
    total_score = (
        0.40 * recall
        + 0.25 * precision
        + 0.15 * severity_accuracy
        + 0.10 * efficiency
        + 0.10 * coverage_quality
    )

    # Clamp to [0.0, 1.0]
    total_score = max(0.0, min(1.0, total_score))

    return {
        "total_score": round(total_score, 4),
        "recall": round(recall, 4),
        "precision": round(precision, 4),
        "severity_accuracy": round(severity_accuracy, 4),
        "efficiency": round(efficiency, 4),
        "coverage_quality": round(coverage_quality, 4),
        "matched_count": len(matched_pairs),
        "total_ground_truth": total_truth,
        "total_findings": total_findings,
        "false_positives": len(false_positives),
        "unmatched_truth_ids": unmatched_truths,
        "matched_details": [
            {
                "truth_id": m["truth"]["id"],
                "match_score": round(m["match_score"], 3),
                "severity_score": round(m["severity_score"], 3),
            }
            for m in matched_pairs
        ],
    }


def compute_step_reward(
    action_type: str,
    finding: Dict[str, Any] | None,
    ground_truth: List[Dict[str, Any]],
    previous_findings: List[Dict[str, Any]],
    step_number: int,
    max_steps: int,
) -> float:
    """Compute reward for a single step action.

    Provides partial progress signal throughout the episode:
    - Correctly identified issues: +0.15 to +0.25
    - Partially matched issues: +0.05 to +0.10
    - False positives (no match): -0.05
    - Requesting relevant sections: +0.02
    - Submitting report: +0.0 to +0.3 based on final score
    - Repeating already-found issues: -0.10
    """
    if action_type == "request_section":
        return 0.02  # Small positive reward for information gathering

    if action_type == "submit_report":
        # Final reward based on overall grade
        grade = grade_episode(previous_findings, ground_truth, step_number, max_steps)
        # Scale terminal reward based on quality
        return grade["total_score"] * 0.3

    if action_type == "identify_issue" and finding:
        finding_text = " ".join([
            str(finding.get("description", "")),
            str(finding.get("section", "")),
            str(finding.get("issue_type", "")),
        ])

        # Check if this finding is a duplicate of something already found
        for prev in previous_findings:
            prev_text = " ".join([
                str(prev.get("description", "")),
                str(prev.get("section", "")),
                str(prev.get("issue_type", "")),
            ])
            # Simple overlap check
            prev_words = set(_normalize(prev_text).split())
            curr_words = set(_normalize(finding_text).split())
            overlap = len(prev_words & curr_words) / max(len(prev_words | curr_words), 1)
            if overlap > 0.6:
                return -0.10  # Penalty for duplicate

        # Check against ground truth
        best_score = 0.0
        best_truth = None
        for truth in ground_truth:
            score = _keyword_match_score(finding_text, truth)
            if score > best_score:
                best_score = score
                best_truth = truth

        if best_score >= 0.5:
            # Good match - scale reward by severity importance
            severity_bonus = {"critical": 0.10, "major": 0.05, "minor": 0.0}
            bonus = severity_bonus.get(best_truth.get("severity", ""), 0.0) if best_truth else 0.0
            return 0.15 + bonus
        elif best_score >= 0.3:
            # Partial match
            return 0.05 + best_score * 0.05
        else:
            # No match - false positive
            return -0.05

    return 0.0  # Unknown action type
