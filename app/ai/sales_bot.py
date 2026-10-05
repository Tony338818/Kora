import json
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from schema.product_schema import ProductCreate

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def build_sales_prompt(message: str, session: dict | None = None) -> str:
    task = (session.get("task") or {}) if session else {}

    session_data = task.get("collected_data", {})
    session_intent = task.get("intent")

    return f"""
You are a STRICT sales transaction extraction engine.

You do NOT chat.
You do NOT explain.
You do NOT guess.

You ONLY:
1. Select ONE intent
2. Extract ONLY explicitly mentioned fields

---

CURRENT SESSION STATE:
task at hand: {task or 'None'}
intent: {session_intent or "None"}

known_data:
{json.dumps(session_data, indent=2)}

---

AVAILABLE INTENTS:

record_sale
record_purchase
get_transaction
list_transactions
generate_receipt

---

FIELD RULES:

- Extract ONLY fields mentioned in THIS message
- NEVER infer missing values
- NEVER copy from session into output

- transaction_type must be: "sale" or "purchase"
- payment_method examples: "cash", "card", "transfer"
- payment_status: "paid", "pending"

- items must be a LIST of objects:
    {{
      "product_name": string,
      "quantity": number,
      "unit_price": number (if mentioned)
    }}

- quantity must be >= 0
- unit_price must be >= 0

---

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "intent": "<one_of_the_intents_or_null>",
  "data": {{}}
}}

---

EXAMPLES:

User: "I sold 2 bags of rice for 10 each cash"
→
{{
  "intent": "record_sale",
  "data": {{
    "transaction_type": "sale",
    "payment_method": "cash",
    "items": [
      {{
        "product_name": "rice",
        "quantity": 2,
        "unit_price": 10
      }}
    ]
  }}
}}

User: "bought 3 beans at 5 each"
→
{{
  "intent": "record_purchase",
  "data": {{
    "transaction_type": "purchase",
    "items": [
      {{
        "product_name": "beans",
        "quantity": 3,
        "unit_price": 5
      }}
    ]
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


def salesbot(message: str, session: dict | None = None) -> dict:
    try:
        prompt = build_sales_prompt(message, session)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        return json.loads(response.text)

    except Exception as e:
        return {"error": 'Could not reach the LLM at this time'}