# import json
# import os

# SESSION_FILE = "sessions.json"


# def _load_sessions():
#     if not os.path.exists(SESSION_FILE):
#         return {}

#     with open(SESSION_FILE, "r") as f:
#         return json.load(f)


# def _save_sessions(sessions):
#     with open(SESSION_FILE, "w") as f:
#         json.dump(sessions, f, indent=2)


# # Get session by phone number
# def get_session(user_id: str) -> dict:
#     sessions = _load_sessions()
#     return sessions.get(user_id, {
#         "intent": None,
#         "class": None,
#         "data": {}
#     })


# # Update / merge session
# def update_session(user_id: str, new_data: dict):
#     sessions = _load_sessions()

#     current = sessions.get(user_id, {
#         "intent": None,
#         "class": None,
#         "data": {}
#     })

#     # merge data safely
#     merged_data = {**current.get("data", {}), **new_data.get("data", {})}

#     sessions[user_id] = {
#         "intent": new_data.get("intent", current.get("intent")),
#         "class": new_data.get("class", current.get("class")),
#         "data": merged_data
#     }

#     _save_sessions(sessions)


# # Clear session after completion
# def clear_session(user_id: str):
#     sessions = _load_sessions()

#     if user_id in sessions:
#         del sessions[user_id]

#     _save_sessions(sessions)

import json
import os

SESSION_FILE = "sessions.json"


def _load_sessions():
    if not os.path.exists(SESSION_FILE):
        return {}

    with open(SESSION_FILE, "r") as f:
        return json.load(f)


def _save_sessions(sessions):
    with open(SESSION_FILE, "w") as f:
        json.dump(sessions, f, indent=2)


def _default_session():
    return {
        "mode": "chat",
        "last_intent": None,
        "history": [],
        "task": None,
        "last_completed_task": None
    }


# Get session
def get_session(user_id: str) -> dict:
    sessions = _load_sessions()
    return sessions.get(user_id, _default_session())


# Update session (safe merge)
def update_session(user_id: str, updates: dict):
    sessions = _load_sessions()
    current = sessions.get(user_id, _default_session())

    # shallow merge for top-level
    for key, value in updates.items():
        if key == "task" and value is not None:
            # merge task separately
            current["task"] = {
                **(current.get("task") or {}),
                **value
            }
        else:
            current[key] = value

    sessions[user_id] = current
    _save_sessions(sessions)


# Append to history
def append_history(user_id: str, entry: dict):
    sessions = _load_sessions()
    current = sessions.get(user_id, _default_session())

    current["history"].append(entry)

    sessions[user_id] = current
    _save_sessions(sessions)


# Clear ONLY task (not whole session)
def clear_task(user_id: str):
    sessions = _load_sessions()
    current = sessions.get(user_id, _default_session())

    if current.get("task"):
        current["last_completed_task"] = current["task"]

    current["task"] = None
    current["mode"] = "chat"

    sessions[user_id] = current
    _save_sessions(sessions)