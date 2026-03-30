# Copyright (c) 2026 Aditya Satapathy
# Clinical Trial Protocol Auditor - OpenEnv Environment
# Models for Action, Observation, and State

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class Action(BaseModel):
    """Base action for the Clinical Trial Protocol Auditor environment.

    The agent can perform three types of actions:
    - identify_issue: Flag a specific compliance/quality issue in the protocol
    - request_section: Request detailed view of a specific protocol section
    - submit_report: Finalize audit and submit findings (ends episode)
    """

    action_type: str = Field(
        ...,
        description="Type of action: 'identify_issue', 'request_section', or 'submit_report'",
    )
    section: Optional[str] = Field(
        None,
        description="Protocol section reference (e.g., 'eligibility_criteria', 'statistical_design')",
    )
    issue_type: Optional[str] = Field(
        None,
        description="Category of issue: 'missing_section', 'logical_inconsistency', 'statistical_error', "
        "'safety_gap', 'regulatory_violation', 'endpoint_issue', 'consent_issue'",
    )
    severity: Optional[str] = Field(
        None,
        description="Issue severity: 'critical', 'major', or 'minor'",
    )
    description: str = Field(
        ...,
        description="Detailed description of the finding or section request",
    )
    recommendation: Optional[str] = Field(
        None,
        description="Suggested corrective action for the identified issue",
    )


class AuditFinding(BaseModel):
    """A single audit finding submitted by the agent."""

    section: str
    issue_type: str
    severity: str
    description: str
    recommendation: Optional[str] = None
    step_number: int = 0
    is_correct: Optional[bool] = None  # Set by grader


class Observation(BaseModel):
    """Observation returned to the agent after each step.

    Contains the protocol text, task context, accumulated findings,
    and feedback from the environment.
    """

    # Core OpenEnv fields
    done: bool = Field(default=False, description="Whether the episode is complete")
    reward: Union[float, None] = Field(default=None, description="Step reward")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Environment-specific fields
    protocol_id: str = Field(..., description="Unique identifier for the current protocol")
    task_id: str = Field(..., description="Current task identifier")
    task_description: str = Field(..., description="Description of what the agent should do")
    protocol_text: str = Field(..., description="The clinical trial protocol text to audit")
    sections_available: List[str] = Field(
        default_factory=list,
        description="List of protocol sections the agent can request",
    )
    identified_issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Issues identified so far in this episode",
    )
    feedback: Optional[str] = Field(
        None,
        description="Feedback from the environment on the last action",
    )
    step_number: int = Field(default=0, description="Current step in the episode")
    max_steps: int = Field(default=15, description="Maximum steps allowed")
    goal: Optional[str] = Field(None, description="High-level goal for the agent")
    url: Optional[str] = Field(None, description="Environment URL (for compatibility)")
    last_action_error: Optional[str] = Field(None, description="Error from last action if any")
    screenshot: Optional[Any] = Field(None, description="Not used in text environment")


class State(BaseModel):
    """Full environment state for checkpointing and debugging."""

    episode_id: str = Field(default="", description="Current episode identifier")
    task_id: str = Field(default="", description="Current task")
    protocol_id: str = Field(default="", description="Current protocol")
    step_count: int = Field(default=0, description="Steps taken")
    max_steps: int = Field(default=15, description="Max steps allowed")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="All findings so far")
    is_done: bool = Field(default=False, description="Episode complete flag")
    cumulative_reward: float = Field(default=0.0, description="Total reward accumulated")
    sections_viewed: List[str] = Field(default_factory=list, description="Sections agent has viewed")
