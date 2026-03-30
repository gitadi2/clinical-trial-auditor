# Copyright (c) 2026 Aditya Satapathy
# Clinical Trial Protocol Auditor - Core Environment Logic
# Implements the OpenEnv Environment interface: reset(), step(), state()

import uuid
from typing import Any, Dict, List, Optional

from .protocols import TASKS, get_task, list_tasks
from .graders import compute_step_reward, grade_episode


class ClinicalTrialAuditorEnvironment:
    """OpenEnv Environment for Clinical Trial Protocol Auditing.

    An AI agent audits clinical trial protocols for compliance issues,
    missing sections, statistical errors, and regulatory violations.

    Tasks (3 difficulty levels):
    - section_completeness (easy): Identify missing/incomplete protocol sections
    - eligibility_validation (medium): Find logical issues in eligibility criteria
    - full_protocol_audit (hard): Comprehensive multi-dimensional audit

    The environment follows the OpenEnv spec with:
    - Typed Pydantic models for actions, observations, and state
    - Meaningful reward function with partial progress signals
    - Deterministic graders scoring 0.0-1.0
    """

    def __init__(self) -> None:
        self._episode_id: str = ""
        self._task_id: str = ""
        self._task: Optional[Dict[str, Any]] = None
        self._step_count: int = 0
        self._max_steps: int = 15
        self._findings: List[Dict[str, Any]] = []
        self._is_done: bool = False
        self._cumulative_reward: float = 0.0
        self._sections_viewed: List[str] = []
        self._last_feedback: Optional[str] = None
        self._last_reward: Optional[float] = None
        self._last_action_error: Optional[str] = None

    def reset(self, task_id: str = "section_completeness", seed: Optional[int] = None) -> Dict[str, Any]:
        """Initialize a new audit episode.

        Args:
            task_id: One of 'section_completeness', 'eligibility_validation', 'full_protocol_audit'
            seed: Optional random seed (deterministic environment, seed unused)

        Returns:
            Initial observation dict
        """
        self._task = get_task(task_id)
        self._episode_id = str(uuid.uuid4())
        self._task_id = task_id
        self._step_count = 0
        self._max_steps = self._task["max_steps"]
        self._findings = []
        self._is_done = False
        self._cumulative_reward = 0.0
        self._sections_viewed = []
        self._last_feedback = "Protocol loaded. Begin your audit by identifying issues or requesting section details."
        self._last_reward = 0.0
        self._last_action_error = None

        return self._build_observation()

    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an audit action and return observation.

        Args:
            action: Dict with keys:
                - action_type: 'identify_issue', 'request_section', or 'submit_report'
                - section: (optional) protocol section reference
                - issue_type: (optional) category of issue
                - severity: (optional) 'critical', 'major', 'minor'
                - description: detailed description
                - recommendation: (optional) suggested fix

        Returns:
            Dict with observation, reward, done, info
        """
        if self._is_done:
            return self._build_observation()

        if self._task is None:
            self._last_action_error = "Environment not initialized. Call reset() first."
            return self._build_observation()

        self._step_count += 1
        self._last_action_error = None
        action_type = action.get("action_type", "").strip().lower()

        # Validate action type
        valid_types = {"identify_issue", "request_section", "submit_report"}
        if action_type not in valid_types:
            self._last_action_error = (
                f"Invalid action_type '{action_type}'. Must be one of: {valid_types}"
            )
            reward = -0.02
            self._last_feedback = self._last_action_error
        elif action_type == "identify_issue":
            reward = self._handle_identify_issue(action)
        elif action_type == "request_section":
            reward = self._handle_request_section(action)
        elif action_type == "submit_report":
            reward = self._handle_submit_report(action)
        else:
            reward = 0.0

        self._last_reward = reward
        self._cumulative_reward += reward

        # Check if max steps reached
        if self._step_count >= self._max_steps and not self._is_done:
            self._is_done = True
            # Auto-grade on max steps
            grade = grade_episode(
                self._findings,
                self._task["ground_truth_issues"],
                self._step_count,
                self._max_steps,
            )
            self._last_feedback = (
                f"Maximum steps reached. Auto-submitting audit report. "
                f"Final score: {grade['total_score']:.3f}"
            )
            # Add terminal reward
            terminal_reward = grade["total_score"] * 0.2
            self._cumulative_reward += terminal_reward
            self._last_reward = reward + terminal_reward

        return self._build_observation()

    @property
    def state(self) -> Dict[str, Any]:
        """Get current environment state for checkpointing."""
        return {
            "episode_id": self._episode_id,
            "task_id": self._task_id,
            "protocol_id": self._task["protocol_id"] if self._task else "",
            "step_count": self._step_count,
            "max_steps": self._max_steps,
            "findings": self._findings.copy(),
            "is_done": self._is_done,
            "cumulative_reward": round(self._cumulative_reward, 4),
            "sections_viewed": self._sections_viewed.copy(),
        }

    def get_tasks(self) -> List[Dict[str, str]]:
        """List available tasks."""
        return list_tasks()

    def grade(self) -> Dict[str, Any]:
        """Grade the current episode."""
        if self._task is None:
            return {"total_score": 0.0, "error": "No active episode"}

        return grade_episode(
            self._findings,
            self._task["ground_truth_issues"],
            self._step_count,
            self._max_steps,
        )

    # ── Internal helpers ──────────────────────────────────────────────

    def _handle_identify_issue(self, action: Dict[str, Any]) -> float:
        """Process an issue identification action."""
        description = action.get("description", "").strip()
        if not description:
            self._last_feedback = "Issue description cannot be empty."
            self._last_action_error = "Empty description"
            return -0.02

        finding = {
            "section": action.get("section", "unspecified"),
            "issue_type": action.get("issue_type", "unspecified"),
            "severity": action.get("severity", "unspecified"),
            "description": description,
            "recommendation": action.get("recommendation", ""),
            "step_number": self._step_count,
        }

        # Compute step reward
        reward = compute_step_reward(
            action_type="identify_issue",
            finding=finding,
            ground_truth=self._task["ground_truth_issues"],
            previous_findings=self._findings,
            step_number=self._step_count,
            max_steps=self._max_steps,
        )

        self._findings.append(finding)

        if reward > 0.1:
            self._last_feedback = (
                f"Issue logged (finding #{len(self._findings)}). "
                f"The finding appears relevant to the protocol audit."
            )
        elif reward > 0:
            self._last_feedback = (
                f"Issue logged (finding #{len(self._findings)}). "
                f"The finding has some relevance but could be more specific."
            )
        elif reward < 0:
            self._last_feedback = (
                f"Issue logged (finding #{len(self._findings)}). "
                f"Warning: this finding may overlap with a previous one or lack specificity."
            )
        else:
            self._last_feedback = f"Issue logged (finding #{len(self._findings)})."

        return reward

    def _handle_request_section(self, action: Dict[str, Any]) -> float:
        """Process a section detail request."""
        section = action.get("section", "").strip().lower()
        if not section:
            self._last_feedback = "Please specify which section to view."
            self._last_action_error = "No section specified"
            return -0.01

        protocol_sections = self._task.get("protocol_sections", {})

        # Try to match section name (fuzzy)
        matched_key = None
        for key in protocol_sections:
            if section in key.lower() or key.lower() in section:
                matched_key = key
                break
            # Also try matching individual words
            if any(word in key.lower() for word in section.split("_")):
                matched_key = key
                break

        if matched_key:
            self._sections_viewed.append(matched_key)
            section_text = protocol_sections[matched_key]
            self._last_feedback = (
                f"=== Section: {matched_key.upper()} ===\n{section_text}"
            )
            return 0.02
        else:
            available = list(protocol_sections.keys())
            # If the section is missing (which IS an issue), that's informative
            self._last_feedback = (
                f"Section '{section}' not found in protocol. "
                f"Note: This could indicate a missing section. "
                f"Available sections: {', '.join(available)}"
            )
            return 0.03  # Slightly higher reward for discovering missing section

    def _handle_submit_report(self, action: Dict[str, Any]) -> float:
        """Process final report submission."""
        self._is_done = True

        grade = grade_episode(
            self._findings,
            self._task["ground_truth_issues"],
            self._step_count,
            self._max_steps,
        )

        reward = compute_step_reward(
            action_type="submit_report",
            finding=None,
            ground_truth=self._task["ground_truth_issues"],
            previous_findings=self._findings,
            step_number=self._step_count,
            max_steps=self._max_steps,
        )

        self._last_feedback = (
            f"Audit report submitted. Final grade: {grade['total_score']:.3f}/1.000\n"
            f"  Recall: {grade['recall']:.3f} ({grade['matched_count']}/{grade['total_ground_truth']} issues found)\n"
            f"  Precision: {grade['precision']:.3f} ({grade['false_positives']} false positives)\n"
            f"  Severity Accuracy: {grade['severity_accuracy']:.3f}\n"
            f"  Efficiency: {grade['efficiency']:.3f}\n"
            f"  Coverage Quality: {grade['coverage_quality']:.3f}"
        )

        return reward

    def _build_observation(self) -> Dict[str, Any]:
        """Build the observation dict returned to the agent."""
        if self._task is None:
            return {
                "done": False,
                "reward": 0.0,
                "metadata": {},
                "protocol_id": "",
                "task_id": "",
                "task_description": "Environment not initialized. Call reset() with a task_id.",
                "protocol_text": "",
                "sections_available": [],
                "identified_issues": [],
                "feedback": "Call reset() to start an episode.",
                "step_number": 0,
                "max_steps": 15,
                "goal": None,
                "url": None,
                "last_action_error": self._last_action_error,
                "screenshot": None,
            }

        sections_available = list(self._task.get("protocol_sections", {}).keys())

        return {
            "done": self._is_done,
            "reward": round(self._last_reward, 4) if self._last_reward is not None else 0.0,
            "metadata": {
                "episode_id": self._episode_id,
                "task_difficulty": self._task.get("difficulty", ""),
                "cumulative_reward": round(self._cumulative_reward, 4),
            },
            "protocol_id": self._task["protocol_id"],
            "task_id": self._task_id,
            "task_description": self._task["description"],
            "protocol_text": self._task["protocol_text"],
            "sections_available": sections_available,
            "identified_issues": [
                {
                    "section": f.get("section", ""),
                    "issue_type": f.get("issue_type", ""),
                    "severity": f.get("severity", ""),
                    "description": f.get("description", ""),
                    "step": f.get("step_number", 0),
                }
                for f in self._findings
            ],
            "feedback": self._last_feedback,
            "step_number": self._step_count,
            "max_steps": self._max_steps,
            "goal": f"Audit protocol {self._task['protocol_id']} - {self._task['name']}",
            "url": None,
            "last_action_error": self._last_action_error,
            "screenshot": None,
        }
