import logging
import re
from uuid import uuid4

from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

from ai.validator import (
    READ_ONLY,
    REQUIRED_SLOTS,
    UPDATE_FIELDS,
    validate_operation,
    validation_issue,
)
from dependency.session import session_service
from dialogue.interpretation import CORRECTION, INVENTORY_COMMAND, explicit_intent, extract_slots
from dialogue.state_tracker import DialogueStateTracker
from schema.conversation_schema import TaskState, TaskStatus
from services.dispatch_service import dispatch


tracker = DialogueStateTracker(session_service, REQUIRED_SLOTS)
logger = logging.getLogger(__name__)
ACTIVE = {TaskStatus.COLLECTING, TaskStatus.READY, TaskStatus.CONFIRMING}
APPROVAL = {"yes", "yes please", "confirm", "confirmed", "go ahead", "approve"}
CANCEL = {"cancel", "cancel task", "stop", "never mind", "nevermind"}
RESTART = {"restart", "start over", "reset"}
REJECT = {"no", "no thanks", "don't confirm"}
FIELD_LABELS = {"name": "product name", "new_name": "new product name", "stock_delta": "change in stock"}
UPDATE_PROMPT = "What should I change? For example, reply 'quantity 12' or 'selling price 4.50'."


def _label(field: str) -> str:
    return FIELD_LABELS.get(field, field.replace("_", " "))


def _question(field: str) -> str:
    return UPDATE_PROMPT if field == "changes" else f"What's the {_label(field)}?"


def _record(state, role: str, content: str):
    state.history.append({"role": role, "content": content})
    state.history = state.history[-tracker.history_limit:]


def _reply(state, message: str, *, success: bool = True):
    _record(state, "assistant", message)
    return {"success": success, "message": message}


def _prediction(model, message: str) -> str:
    labels, _ = model.predict(" ".join(message.split()))
    return labels[0].removeprefix("__label__").lower() if len(labels) else ""


def _route(message, task, models):
    explicit = explicit_intent(message)
    if explicit:
        return explicit, "sales_conversation"

    if task.status in ACTIVE and task.intent in REQUIRED_SLOTS:
        field_edit = re.match(r"^(?:change|set) (?:the )?(?:quantity|stock|cost price|selling price|unit price)\s+(?:to|by)\b", message, re.I)
        command = not field_edit and not CORRECTION.match(message) and INVENTORY_COMMAND.match(message)
        if not command:
            return task.intent, task.message_class
        intent = _prediction(models.inventory_classifier, message)
        return (intent, "inventory") if intent in REQUIRED_SLOTS else (task.intent, task.message_class)

    category = _prediction(models.conversation_classifier, message)
    if category in {"inventory", "inventory_conversation"} or INVENTORY_COMMAND.match(message):
        return _prediction(models.inventory_classifier, message), "inventory"
    return None, category


def _confirmation(intent: str, slots: dict) -> str:
    details = ", ".join(
        f"{_label(field)} = {value}" for field, value in slots.items()
        if field in {*REQUIRED_SLOTS[intent], *UPDATE_FIELDS, "product_id"}
    )
    action = intent.replace("_", " ").capitalize()
    return f"{action} ({details}). Reply yes to confirm, cancel to stop, or tell me what to change."


def _handle_turn(state, message, models, seen_confirmation):
    task = state.task
    state.last_message = message
    _record(state, "user", message)
    command = message.lower().strip(" .!?")

    if task.status == TaskStatus.EXECUTING:
        return "reply", _reply(state, "I'm processing your previous request.")
    if command in CANCEL | RESTART:
        state.task = TaskState()
        state.mode = "chat"
        state.last_intent = None
        response = "Cancelled." if command in CANCEL else "Conversation restarted. What would you like to do?"
        return "reply", _reply(state, response)
    if command in APPROVAL:
        if (task.status == TaskStatus.CONFIRMING and task.confirmation_id
                and task.confirmation_id == seen_confirmation):
            data = validate_operation(task.intent, task.slots)
            action = tracker.transition(state, message, None, {}, event="execution_started")
            return "execute", (action.intent, data)
        if task.status == TaskStatus.CONFIRMING:
            return "reply", _reply(state, _confirmation(task.intent, task.slots))
        if task.missing_slots:
            return "reply", _reply(state, _question(task.missing_slots[0]))
        return "reply", _reply(state, "There's no request waiting for confirmation.")
    if command in REJECT and task.status == TaskStatus.CONFIRMING:
        task.status = TaskStatus.COLLECTING
        task.confirmation_id = None
        return "reply", _reply(state, "What would you like to change? You can also reply cancel.")

    intent, category = _route(message, task, models)
    if intent is None:
        return "chat", None
    if intent not in REQUIRED_SLOTS:
        return "reply", _reply(state, "I couldn't identify the operation. What would you like to do?", success=False)

    same_task = task.intent == intent and task.status in ACTIVE
    pending = task.missing_slots[0] if same_task and task.missing_slots else None
    slots = extract_slots(message, intent, pending, models, continuing=same_task)
    if slots.get("multiple_items"):
        return "reply", _reply(state, "Please send one product per sale or purchase.", success=False)
    if same_task:
        if "stock_delta" in slots:
            for field in UPDATE_FIELDS - {"stock_delta"}:
                task.slots.pop(field, None)
        elif UPDATE_FIELDS.intersection(slots):
            task.slots.pop("stock_delta", None)
        if "name" in slots:
            task.slots.pop("product_id", None)
        if "product_id" in slots:
            task.slots.pop("name", None)
        if task.status == TaskStatus.CONFIRMING and all(task.slots.get(key) == value for key, value in slots.items()):
            return "reply", _reply(state, _confirmation(intent, task.slots))
        if not slots and not pending and task.status == TaskStatus.COLLECTING:
            return "reply", _reply(state, "Tell me the field and its new value, or reply cancel.")

    action = tracker.transition(state, message, intent, slots)
    task = state.task
    task.message_class = category
    task.confirmation_id = None
    if action.missing_slots:
        return "reply", _reply(state, _question(action.missing_slots[0]))
    if intent == "update_product" and not UPDATE_FIELDS.intersection(task.slots):
        task.status = TaskStatus.COLLECTING
        task.missing_slots = ["changes"]
        return "reply", _reply(state, UPDATE_PROMPT)

    try:
        data = validate_operation(intent, task.slots)
    except ValidationError as error:
        field, problem = validation_issue(error, intent)
        task.status = TaskStatus.COLLECTING
        task.missing_slots = [field]
        return "reply", _reply(state, f"{_label(field).capitalize()} {problem.lower()}. {_question(field)}", success=False)

    if intent in READ_ONLY:
        task.confirmation_id = uuid4().hex
        tracker.transition(state, message, None, {}, event="execution_started")
        return "execute", (intent, data)

    task.status = TaskStatus.CONFIRMING
    task.confirmation_id = uuid4().hex
    return "reply", _reply(state, _confirmation(intent, task.slots))


def _chat(message, state):
    from ai.chatbot import chatbot

    return chatbot(message, state.model_dump()) or "Hi! How can I help you today?"


async def process_message(db, user_id: int, message: str, session_id: str, request, message_id: str | None = None):
    message = message.strip()
    if not message:
        return {"success": False, "message": "Please send a message with your request."}

    first_attempt = True
    seen_confirmation = None

    def transition(state):
        nonlocal first_attempt, seen_confirmation
        if first_attempt:
            seen_confirmation = state.task.confirmation_id
            first_attempt = False
        return _handle_turn(state, message, request.app.state, seen_confirmation)

    state, action = await session_service.update(session_id, transition, message_id=message_id)
    if action is None:
        return {"success": True, "duplicate": True}
    kind, payload = action
    if kind == "reply":
        return payload
    if kind == "chat":
        response = await run_in_threadpool(_chat, message, state)
        _, result = await session_service.update(session_id, lambda current: _reply(current, response))
        return result

    intent, data = payload
    try:
        result = dispatch(db, user_id, intent, data)
    except Exception:
        db.rollback()
        logger.exception("Dialogue operation %s failed", intent)
        result = {"success": False, "message": "I couldn't verify the result. Check your records before trying again."}

    def complete(current):
        if current.task.status == TaskStatus.EXECUTING and current.task.confirmation_id == state.task.confirmation_id:
            tracker.transition(current, message, None, {}, event="execution_succeeded")
        response = result.get("message")
        if not response and isinstance(result.get("data"), str):
            response = result["data"]
        return _reply(current, response or "Done.", success=result["success"])

    _, reply = await session_service.update(session_id, complete)
    return reply
