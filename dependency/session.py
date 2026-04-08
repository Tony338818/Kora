import time
from typing import Dict

# ─── CONFIG ─────────────────────────────────────────────────────

SESSION_TIMEOUT = 600

# ─── IN-MEMORY STORE ────────────────────────────────────────────

sessions: Dict[str, dict] = {}

# ─── HELPERS ────────────────────────────────────────────────────

def _now():
    return time.time()


def _default_session():
    return {
        "mode": "chat",
        "last_intent": None,
        "history": [],
        "task": None,
        "last_completed_task": None
    }


def _is_expired(last_seen: float) -> bool:
    return (_now() - last_seen) > SESSION_TIMEOUT


def _cleanup_expired():
    """Remove expired sessions (lazy cleanup)."""
    expired_users = [
        user_id for user_id, session in sessions.items()
        if _is_expired(session["last_seen"])
    ]

    for user_id in expired_users:
        del sessions[user_id]

# ─── CORE FUNCTIONS ─────────────────────────────────────────────

def get_session(user_id: str) -> dict:
    _cleanup_expired()

    session_obj = sessions.get(user_id)

    if not session_obj:
        # create new session
        sessions[user_id] = {
            "data": _default_session(),
            "last_seen": _now()
        }
        return sessions[user_id]["data"]

    # check expiry
    if _is_expired(session_obj["last_seen"]):
        sessions[user_id] = {
            "data": _default_session(),
            "last_seen": _now()
        }
        return sessions[user_id]["data"]

    # update activity timestamp
    session_obj["last_seen"] = _now()

    return session_obj["data"]


def update_session(user_id: str, updates: dict):
    session = get_session(user_id)

    # merge updates
    for key, value in updates.items():
        if key == "task" and value is not None:
            session["task"] = {
                **(session.get("task") or {}),
                **value
            }
        else:
            session[key] = value

    # update timestamp
    sessions[user_id]["last_seen"] = _now()


def append_history(user_id: str, entry: dict):
    session = get_session(user_id)

    session["history"].append(entry)

    sessions[user_id]["last_seen"] = _now()


def clear_task(user_id: str):
    session = get_session(user_id)

    if session.get("task"):
        session["last_completed_task"] = session["task"]

    session["task"] = None
    session["mode"] = "chat"

    sessions[user_id]["last_seen"] = _now()