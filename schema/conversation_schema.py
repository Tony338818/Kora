from pydantic import BaseModel, Field
from typing import Optional


class TaskState(BaseModel):

    intent: Optional[str] = None
    status: str = "idle"
    slots: dict = Field(default_factory=dict)



class ConversationState(BaseModel):

    user_id: str
    mode: str = "chat"
    last_intent: Optional[str] = None
    last_message: Optional[str] = None
    task: TaskState = Field(
        default_factory=TaskState
    )
    history: list = Field(
        default_factory=list
    )