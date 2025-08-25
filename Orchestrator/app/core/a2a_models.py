from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class AgentCard(BaseModel):
    id: str
    name: str
    description: str
    capabilities: List[str] = Field(default_factory=list)
    version: str = "0.1.0"


class TaskInput(BaseModel):
    logs: str
    context: Optional[Dict[str, Any]] = None


class TaskResult(BaseModel):
    status: Literal["ok", "error", "needs_support"]
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)


class Event(BaseModel):
    type: Literal[
        "task.created",
        "task.started",
        "agent.started",
        "agent.completed",
        "delegation.requested",
        "delegation.completed",
        "task.completed",
        "error",
    ]
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    id: str
    agent_id: str
    input: TaskInput


class Delegation(BaseModel):
    from_agent_id: str
    to_agent_id: str
    reason: str
    input_override: Optional[TaskInput] = None
