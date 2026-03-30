# Copyright (c) 2026 Aditya Satapathy
# Clinical Trial Protocol Auditor - Client
# Typed client for interacting with the Clinical Trial Auditor environment

import requests
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class StepResult:
    """Result of a step or reset call."""
    observation: Dict[str, Any]
    reward: float = 0.0
    done: bool = False
    info: Dict[str, Any] = field(default_factory=dict)


class ClinicalTrialAuditorClient:
    """HTTP client for the Clinical Trial Protocol Auditor environment.

    Usage:
        client = ClinicalTrialAuditorClient(base_url="http://localhost:7860")
        result = client.reset(task_id="section_completeness")
        result = client.step(
            action_type="identify_issue",
            section="statistical_design",
            issue_type="missing_section",
            severity="critical",
            description="Statistical analysis plan section is completely missing.",
        )
        state = client.state()
        grade = client.grade()
    """

    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")

    def reset(self, task_id: str = "section_completeness", seed: Optional[int] = None) -> StepResult:
        """Reset environment and start new episode."""
        resp = requests.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id, "seed": seed},
        )
        resp.raise_for_status()
        data = resp.json()
        return StepResult(
            observation=data.get("observation", {}),
            reward=data.get("reward", 0.0),
            done=data.get("done", False),
            info=data.get("info", {}),
        )

    def step(
        self,
        action_type: str,
        description: str,
        section: Optional[str] = None,
        issue_type: Optional[str] = None,
        severity: Optional[str] = None,
        recommendation: Optional[str] = None,
    ) -> StepResult:
        """Execute an action in the environment."""
        resp = requests.post(
            f"{self.base_url}/step",
            json={
                "action_type": action_type,
                "section": section,
                "issue_type": issue_type,
                "severity": severity,
                "description": description,
                "recommendation": recommendation,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return StepResult(
            observation=data.get("observation", {}),
            reward=data.get("reward", 0.0),
            done=data.get("done", False),
            info=data.get("info", {}),
        )

    def state(self) -> Dict[str, Any]:
        """Get current environment state."""
        resp = requests.get(f"{self.base_url}/state")
        resp.raise_for_status()
        return resp.json()

    def grade(self) -> Dict[str, Any]:
        """Grade current episode."""
        resp = requests.get(f"{self.base_url}/grade")
        resp.raise_for_status()
        return resp.json()

    def tasks(self) -> List[Dict[str, str]]:
        """List available tasks."""
        resp = requests.get(f"{self.base_url}/tasks")
        resp.raise_for_status()
        return resp.json().get("tasks", [])
