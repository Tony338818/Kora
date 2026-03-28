import json
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from schema.model_schema import Conversation

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Chatbot Prompt
def build_chat_prompt(message: str, session: dict | None = None) -> str:
    task           = (session.get("task") or {}) if session else {}
    session_data   = task.get("collected_data", {})
    session_intent = task.get("intent")
    mode           = session.get("mode") if session else None

    return f"""
You are a CONTROLLED retail assistant.

You are friendly, but you are TASK-FOCUSED.
You do NOT ramble, joke excessively, or go off-topic.

---

CURRENT SESSION:

intent: {session_intent or "None"}

known_data:
{json.dumps(session_data, indent=2)}

---

YOUR BEHAVIOR RULES:

1. ALWAYS keep responses under 2 sentences
2. Be natural, but direct
3. NEVER explain system capabilities unless asked
4. NEVER hallucinate data
5. NEVER ask multiple questions at once

---

TASK HANDLING RULES:

IF there is an active intent:
- Your job is to COMPLETE the task
- Identify missing required fields
- Ask for ONLY ONE missing field at a time
- Be specific

Example:
Bad → "Please provide more details"
Good → "What is the selling price?"

IF product name exists:
- Use it in your response

Example:
"How many units of rice?"

---

IF NO ACTIVE INTENT:

- If user message is casual → respond briefly and naturally
- Then gently steer toward system usage

Example:
User: "how are you"
→ "I'm good! What would you like to do—add stock or check inventory?"

---

IF USER IS UNCLEAR:

- Ask a clarifying question
- Do NOT assume intent

Example:
User: "yes"
→ "Can you tell me what you'd like to do?"

---

TONE:

- Calm
- Professional
- Slightly friendly
- Not playful

---

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "message": "<response>"
}}

---

USER MESSAGE:
"{message}"

OUTPUT:
"""

def chatbot(message: str, session: dict) -> str:
    try:
        # Pass the session into the prompt builder
        prompt = build_chat_prompt(message, session)
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                # Using system_instruction for the "rules" keeps the logic stable
                system_instruction="You are a helpful retail assistant. Contextualize your answers using the provided session data.",
                response_mime_type="application/json",
                temperature=0.7,
                response_schema=Conversation
            )
        )
        result = json.loads(response.text)
        return result.get("message")

    except Exception as e:
        print(f"Error: {e}")
        return "Hi! How can I help you today?"