import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_prompt(message: str, session: dict | None = None):
    return f"""
You are an AI assistant for a retail management system.

Your job:
1. Identify CLASS (Inventory or Sales)
2. Identify INTENT
3. Extract structured data from the user's message
4. Return a clarification if required data is missing

You are part of a multi-turn conversation. Use the session state below to fill in
fields the user already provided in earlier messages — do NOT ask for them again.

---

SESSION STATE:
{json.dumps(session, indent=2) if session else "None"}

---

CLASSES:

Inventory → Product-related actions
Sales     → Transactions, receipts, analytics

---

INVENTORY INTENTS:

add_product                  → Add a new product
increment_stock_quantity     → Increase stock count
decrement_stock_quantity     → Decrease stock count
update_cost_price            → Change cost price
update_selling_price         → Change selling price
get_product_info             → Get details of a product
view_inventory               → List all products
change_product_availability  → Mark product as available/unavailable
delete_product               → Remove a product

---

SALES INTENTS:

record_sale          → Record a completed sale
generate_receipt     → Get or create a receipt
get_transaction      → Retrieve a specific transaction
list_transactions    → View transaction history
sales_analytics      → Sales insights (time_range: daily | weekly | monthly)
top_selling_products → Best performing products
refund_transaction   → Refund a transaction
void_transaction     → Void a transaction

---

STRICT RULES:

- NEVER guess or invent values — only extract what the user explicitly stated
- NEVER ask for optional fields (supplier, img_url, description, buy_date, expiry_date)
- Use session state to fill gaps from previous messages
- If intent is unclear → return type = "unknown"
- If intent is clear but required fields are still missing → return type = "clarification"
- If all required fields are present → return type = "final"

---

PRODUCT SCHEMA (for add_product):

Required : name (str), quantity (int >= 0), cost_price (float >= 0), selling_price (float >= 0)
Optional : supplier, img_url, description, buy_date, expiry_date

---

REQUIRED FIELDS PER INTENT:

Inventory:
  add_product                 → name, quantity, cost_price, selling_price
  increment_stock_quantity    → name, quantity
  decrement_stock_quantity    → name, quantity
  update_cost_price           → name, cost_price
  update_selling_price        → name, selling_price
  get_product_info            → name
  change_product_availability → name, available (bool)
  delete_product              → name
  view_inventory              → (none)

Sales:
  record_sale          → items: [ {{ name, quantity }} ]
  get_transaction      → transaction_id
  refund_transaction   → transaction_id
  void_transaction     → transaction_id
  list_transactions    → (none)
  sales_analytics      → (none)
  top_selling_products → (none)

---

RESPONSE FORMAT — return only valid JSON, no extra text:

1. All required fields present:
{{
  "type": "final",
  "class": "Inventory | Sales",
  "intent": "<intent_name>",
  "data": {{ <extracted fields only> }},
  "confidence": <0.0 – 1.0>
}}

2. Intent clear but required fields missing:
{{
  "type": "clarification",
  "class": "Inventory | Sales",
  "intent": "<intent_name>",
  "message": "<one natural, concise question to the user>",
  "missing_fields": ["field1", "field2"],
  "data": {{ <whatever was already extracted> }}
}}

3. Intent unclear:
{{
  "type": "unknown",
  "message": "<short friendly message asking them to rephrase>"
}}

---

EXAMPLES:

User: "I sell basmati rice, I buy at $5 and sell at $5.40"
→
{{
  "type": "clarification",
  "class": "Inventory",
  "intent": "add_product",
  "message": "How many units of basmati rice do you currently have in stock?",
  "missing_fields": ["quantity"],
  "data": {{ "name": "basmati rice", "cost_price": 5.0, "selling_price": 5.4 }}
}}

---

User: "I have 200 bags"
(session already has name, cost_price, selling_price)
→
{{
  "type": "final",
  "class": "Inventory",
  "intent": "add_product",
  "data": {{
    "name": "basmati rice",
    "quantity": 200,
    "cost_price": 5.0,
    "selling_price": 5.4
  }},
  "confidence": 0.97
}}

---

User input:
"{message}"

Output:
"""


def recognize_intent(message: str, session: dict) -> dict:
    try:
        prompt = build_prompt(message, session)

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
                system_instruction="You are an AI assistant for a retail management system."
            )
        )

        return json.loads(response.text)

    except Exception as e:
        return {
            "type": "error",
            "message": str(e)
        }