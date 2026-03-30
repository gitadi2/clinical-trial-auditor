# Copyright (c) 2026 Aditya Satapathy
# Clinical Trial Protocol Auditor - FastAPI Server
# Implements OpenEnv HTTP API: /reset, /step, /state, /tasks, /grade

import os
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .environment import ClinicalTrialAuditorEnvironment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── FastAPI App ───────────────────────────────────────────────────────────

app = FastAPI(
    title="Clinical Trial Protocol Auditor",
    description=(
        "An OpenEnv environment where AI agents audit clinical trial protocols "
        "for compliance issues, missing sections, statistical errors, and "
        "regulatory violations. Implements the full OpenEnv spec with typed "
        "models, step/reset/state API, and deterministic graders."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-session environments (simple single-session for HF Space)
# For production, use session management
env = ClinicalTrialAuditorEnvironment()


# ── Request/Response Models ───────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = Field(
        default="section_completeness",
        description="Task to load: 'section_completeness' (easy), "
        "'eligibility_validation' (medium), or 'full_protocol_audit' (hard)",
    )
    seed: Optional[int] = Field(default=None, description="Random seed (unused, env is deterministic)")


class StepRequest(BaseModel):
    action_type: str = Field(
        ...,
        description="Action type: 'identify_issue', 'request_section', or 'submit_report'",
    )
    section: Optional[str] = Field(
        None,
        description="Protocol section reference",
    )
    issue_type: Optional[str] = Field(
        None,
        description="Issue category: 'missing_section', 'logical_inconsistency', "
        "'statistical_error', 'safety_gap', 'regulatory_violation', "
        "'endpoint_issue', 'consent_issue'",
    )
    severity: Optional[str] = Field(None, description="Severity: 'critical', 'major', 'minor'")
    description: str = Field(..., description="Detailed description of finding or request")
    recommendation: Optional[str] = Field(None, description="Suggested corrective action")


class ObservationResponse(BaseModel):
    observation: Dict[str, Any]
    reward: float = 0.0
    done: bool = False
    info: Dict[str, Any] = Field(default_factory=dict)


# ── API Endpoints ─────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check and environment info."""
    return {
        "name": "Clinical Trial Protocol Auditor",
        "version": "1.0.0",
        "spec": "openenv",
        "status": "ready",
        "description": (
            "AI agents audit clinical trial protocols for compliance issues, "
            "missing sections, statistical errors, and regulatory violations."
        ),
        "tasks": env.get_tasks(),
    }


@app.get("/health")
async def health():
    """Health check endpoint for HF Spaces."""
    return {"status": "healthy"}


@app.post("/reset")
async def reset(request: ResetRequest = ResetRequest()):
    """Reset the environment and start a new audit episode.

    Available tasks:
    - section_completeness (easy): Find missing protocol sections
    - eligibility_validation (medium): Find logical issues in eligibility criteria
    - full_protocol_audit (hard): Comprehensive audit of a gene therapy protocol
    """
    try:
        observation = env.reset(task_id=request.task_id, seed=request.seed)
        return ObservationResponse(
            observation=observation,
            reward=0.0,
            done=False,
            info={"episode_id": observation.get("metadata", {}).get("episode_id", "")},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
async def step(request: StepRequest):
    """Execute an audit action in the environment.

    Action types:
    - identify_issue: Flag a specific issue in the protocol
    - request_section: Request detailed view of a protocol section
    - submit_report: Finalize the audit (ends episode)
    """
    try:
        action = {
            "action_type": request.action_type,
            "section": request.section,
            "issue_type": request.issue_type,
            "severity": request.severity,
            "description": request.description,
            "recommendation": request.recommendation,
        }
        observation = env.step(action)
        return ObservationResponse(
            observation=observation,
            reward=observation.get("reward", 0.0),
            done=observation.get("done", False),
            info=observation.get("metadata", {}),
        )
    except Exception as e:
        logger.error(f"Step error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_state():
    """Get current environment state for checkpointing/debugging."""
    try:
        return env.state
    except Exception as e:
        logger.error(f"State error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks")
async def get_tasks():
    """List all available audit tasks with metadata."""
    return {"tasks": env.get_tasks()}


@app.get("/grade")
async def grade():
    """Grade the current episode and return detailed scoring breakdown."""
    try:
        return env.grade()
    except Exception as e:
        logger.error(f"Grade error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Startup ───────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info("Clinical Trial Protocol Auditor environment ready.")
    logger.info(f"Available tasks: {[t['id'] for t in env.get_tasks()]}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
