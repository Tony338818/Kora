
from typing import Any

from schema.conversation_schema import (
    ConversationState,
    TaskStatus,
)


class ContextResolver:

    def resolve(
        self,
        state: ConversationState,
        intent: str | None,
        slots: dict[str, Any],  
    ) -> tuple[str | None, dict[str, Any]]:
        task = state.task
        resolved = dict(slots)

        active = task.status in {
            TaskStatus.COLLECTING,
            TaskStatus.READY,
            TaskStatus.CONFIRMING,
        }

        if not active:
            return intent, resolved

        # An explicit different intent starts a new task.
        if intent is not None and intent != task.intent:
            return intent, resolved

        # Continue the existing task if no new intent is supplied.
        if intent is None:
            intent = task.intent

        return intent, resolved
