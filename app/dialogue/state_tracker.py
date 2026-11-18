
from typing import Any, Literal

from dialogue.context_resolver import ContextResolver
from schema.conversation_schema import (
    ConversationState,
    NextAction,
    TaskState,
    TaskStatus,
)
from services.session_service import SessionService


Event = Literal[
    "message",
    "cancel",
    "execution_started",
    "execution_succeeded",
    "execution_failed",
]


class DialogueStateTracker:

    def __init__(
        self,
        sessions: SessionService,
        required_slots: dict[str, list[str]],
        history_limit: int = 100,
    ):
        if history_limit < 1:
            raise ValueError("history_limit must be positive")

        self.sessions = sessions
        self.required_slots = required_slots
        self.history_limit = history_limit
        self.context_resolver = ContextResolver()

    async def handle_message(
        self,
        user_id: str,
        message: str,
        *,
        intent: str | None = None,
        slots: dict[str, Any] | None = None,
        event: Event = "message",
    ):
        return await self.sessions.update(
            user_id,
            lambda state: self.transition(
                state=state,
                message=message,
                intent=intent,
                slots=slots or {},
                event=event,
            ),
        )

    def transition(
        self,
        state: ConversationState,
        message: str,
        intent: str | None,
        slots: dict[str, Any],
        event: Event = "message",
    ) -> NextAction:

        if event not in {
            "message",
            "cancel",
            "execution_started",
            "execution_succeeded",
            "execution_failed",
        }:
            raise ValueError("Unsupported event")

        if event == "cancel":
            if state.task.status not in {
                TaskStatus.COLLECTING,
                TaskStatus.READY,
                TaskStatus.CONFIRMING,
            }:
                return NextAction(action="chat")

            previous_intent = state.task.intent
            state.task = TaskState()
            state.mode = "chat"

            return NextAction(
                action="task_cancelled",
                intent=previous_intent,
            )

        if event == "execution_started":
            if state.task.status not in {TaskStatus.READY, TaskStatus.CONFIRMING}:
                raise ValueError("Task is not ready")

            state.task.status = TaskStatus.EXECUTING
            return NextAction(
                action="execute",
                intent=state.task.intent,
                data=state.task.slots.copy(),
            )

        if event == "execution_succeeded":
            if state.task.status != TaskStatus.EXECUTING:
                raise ValueError("Task is not executing")

            previous_intent = state.task.intent
            state.task = TaskState(status=TaskStatus.COMPLETED)
            state.mode = "chat"

            return NextAction(
                action="task_completed",
                intent=previous_intent,
            )

        if event == "execution_failed":
            if state.task.status != TaskStatus.EXECUTING:
                raise ValueError("Task is not executing")

            state.task.status = TaskStatus.FAILED
            state.mode = "chat"

            return NextAction(
                action="task_failed",
                intent=state.task.intent,
            )

        if state.task.status == TaskStatus.EXECUTING:
            return NextAction(
                action="task_busy",
                intent=state.task.intent,
            )

        intent, slots = self.context_resolver.resolve(
            state, intent, slots
        )

        if intent is None:
            return NextAction(action="chat")

        if intent not in self.required_slots:
            return NextAction(
                action="unknown_intent",
                intent=intent,
            )

        state.last_intent = intent

        if (
            intent != state.task.intent
            or state.task.status not in {
                TaskStatus.COLLECTING,
                TaskStatus.READY,
                TaskStatus.CONFIRMING,
            }
        ):
            state.task = TaskState(
                intent=intent,
                status=TaskStatus.COLLECTING,
            )

        state.mode = "task"

        # Only supplied fields are updated.
        # None explicitly clears a field.
        state.task.slots.update(slots)

        missing = [
            field
            for field in self.required_slots[intent]
            if self._missing(state.task.slots.get(field))
            and not (field == "name" and state.task.slots.get("product_id"))
        ]

        state.task.missing_slots = missing

        if missing:
            state.task.status = TaskStatus.COLLECTING

            return NextAction(
                action="ask_slot",
                intent=intent,
                slot=missing[0],
                missing_slots=missing,
            )

        state.task.status = TaskStatus.READY

        return NextAction(
            action="task_ready",
            intent=intent,
            data=state.task.slots.copy(),
        )

    @staticmethod
    def _missing(value: Any) -> bool:
        return (
            value is None
            or (
                isinstance(value, str)
                and not value.strip()
            )
        )
