import json
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from schema.product_schema import ProductCreate

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def build_inventory_prompt(message: str, session: dict | None = None) -> str:
    task           = (session.get("task") or {}) if session else {}
    session_data   = task.get("collected_data", {})
    session_intent = task.get("intent")

    return f"""
You are a STRICT inventory extraction engine.

You do NOT chat.
You do NOT explain.
You do NOT guess.

You ONLY:
1. Select ONE intent
2. Extract ONLY explicitly mentioned fields

---

CURRENT SESSION STATE:
task at hand: {task}
intent: {session_intent or "None"}

known_data:
{json.dumps(session_data, indent=2)}

---

INTENT RULES:

1. If session intent exists → KEEP IT unless user clearly changes topic
2. If no intent → choose the MOST obvious intent
3. If message is ambiguous → return:
   {{
     "intent": null,
     "data": {{}}
   }}

---

AVAILABLE INTENTS:

add_product
increment_stock_quantity
decrement_stock_quantity
update_cost_price
update_selling_price
get_product_info
change_product_availability
delete_product
view_inventory

---

FIELD RULES:

- Extract ONLY fields mentioned in THIS message
- NEVER infer missing values
- NEVER copy from session into output
- quantity must be >= 0
- prices must be >= 0
- name must be lowercase string
- dates must be ISO 8601 format

---

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "intent": "<one_of_the_intents_or_null>",
  "data": {{}}
}}

---

EXAMPLES:

User: "add 50 bags of rice at 20 sell 25"
→
{{
  "intent": "add_product",
  "data": {{
    "name": "rice",
    "quantity": 50,
    "cost_price": 20,
    "selling_price": 25
  }}
}}

User: "increase yam by 30"
→
{{
  "intent": "increment_stock_quantity",
  "data": {{
    "name": "yam",
    "quantity": 30
  }}
}}

User: "how many eggs do I have"
→
{{
  "intent": "get_product_info",
  "data": {{
    "name": "eggs"
  }}
}}

User: "yes"
→
{{
  "intent": null,
  "data": {{}}
}}

---

USER MESSAGE:
"{message}"

OUTPUT:
"""


def inventorybot(message: str, session: dict | None = None) -> dict:
    try:
        prompt = build_inventory_prompt(message, session)
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return json.loads(response.text)

    except Exception as e:
        return {"error": 'Could not reach the LLM at this time'}