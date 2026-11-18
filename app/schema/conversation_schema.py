from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    IDLE = "idle"
    COLLECTING = "collecting"
    CONFIRMING = "confirming"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskState(BaseModel):
    intent: str | None = None
    message_class: str | None = None
    status: TaskStatus = TaskStatus.IDLE
    slots: dict[str, Any] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    confirmation_id: str | None = None


class ConversationState(BaseModel):
    user_id: str
    mode: str = "chat"

    last_intent: str | None = None
    last_message: str | None = None

    task: TaskState = Field(default_factory=TaskState)
    history: list[dict[str, str]] = Field(default_factory=list)

    version: int = 0


class NextAction(BaseModel):
    action: str
    intent: str | None = None
    slot: str | None = None
    missing_slots: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
