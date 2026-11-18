import re

from ai.validator import PRODUCT_LOOKUPS, SALES
from utils.normalize_model_output import ENTITY_MAP


NUMBER = r"[-+]?\d[\d,]*(?:\.\d+)?"
CURRENCY = r"[£$€₦]?\s*"
PRICE_TARGET = r"(?:\s+of\s+(?:product|item)\s+#?\d+)?"
FIELD_PATTERNS = {
    "cost_price": rf"\b(?:cost(?: price)?|buying price){PRICE_TARGET}\s*(?:is|to|at|=|:)?\s*{CURRENCY}({NUMBER})",
    "selling_price": rf"(?<!cost )(?<!buying )\b(?:selling price|sell(?:ing)?(?: at)?|price){PRICE_TARGET}\s*(?:is|to|=|:)?\s*{CURRENCY}({NUMBER})",
    "quantity": rf"\b(?:quantity|stock)\s*(?:is|to|=|:)?\s*({NUMBER})",
    "new_name": r"\b(?:new name|name to|rename to)\s*(?:=|:)?\s*(.+)$",
    "payment_method": r"\b(cash|card|(?:bank )?transfer|mobile money)\b",
    "payment_status": r"\b(unpaid|not paid|paid)\b",
    "unit_price": rf"\b(?:unit price|at)\s*(?:is|to|=|:)?\s*{CURRENCY}({NUMBER})",
}
NUMBER_FIELDS = {"quantity", "product_id", "transaction_id", "cost_price", "selling_price", "unit_price", "stock_delta"}
INVENTORY_COMMAND = re.compile(
    r"^(?:(?:please|i want to|can you|could you)\s+)*"
    r"(?:add|stock|restock|update|change|modify|adjust|increase|decrease|reduce|"
    r"delete|remove|rename|show|list|view|check|get|how many|what is the price)\b",
    re.I,
)
BUSINESS_ROUTES = (
    (r"^(?:list|show|view) (?:all |my )?transactions\b", "list_transactions"),
    (r"^(?:please\s+)?(?:(?:generate|get|show|send) (?:a |the )?)?receipt(?:\s+(?:for|id|#?\d)|[.!?]*$)", "generate_receipt"),
    (r"\b(?:get|show|view|check) (?:the )?transaction\b", "get_transaction"),
    (r"\b(?:sold|customer (?:bought|purchased)|record (?:a )?sale|log (?:a |this )?sale)\b", "record_sale"),
    (r"\b(?:record (?:a )?purchase|log (?:a |this )?purchase|we (?:bought|purchased)|i (?:bought|purchased))\b", "record_purchase"),
)
CORRECTION = re.compile(r"^(?:actually|correction|instead)\b[,:\s]*", re.I)


def explicit_intent(message: str) -> str | None:
    return next((intent for pattern, intent in BUSINESS_ROUTES if re.search(pattern, message, re.I)), None)


def extract_slots(message: str, intent: str, pending: str | None, models, *, continuing: bool) -> dict:
    text = CORRECTION.sub("", message).strip()
    lower = text.lower()
    slots = {}

    if intent in {"view_inventory", "list_transactions"}:
        return slots
    if intent in {"get_transaction", "generate_receipt"}:
        match = re.search(r"\b(?:transaction|receipt)(?:\s+(?:id|for(?: transaction)?))?\s*#?\s*(" + NUMBER + r")\b", lower)
        if match:
            slots["transaction_id"] = match[1].replace(",", "")
        elif pending and re.fullmatch(rf"#?\s*{NUMBER}", lower):
            slots["transaction_id"] = lower.lstrip("# ").replace(",", "")
        return slots

    for field, pattern in FIELD_PATTERNS.items():
        if (field in {"payment_method", "payment_status", "unit_price"}) != (intent in SALES):
            continue
        match = re.search(pattern, lower)
        if match:
            slots[field] = match[1].replace(",", "") if field in NUMBER_FIELDS else match[1]
    if slots.get("payment_status") == "not paid":
        slots["payment_status"] = "unpaid"
    stock_change = (
        re.search(r"\b(?:stock|quantity)\b", lower)
        or re.match(r"(?:increase|decrease|reduce|adjust)\b", lower)
    )
    relative = None
    if intent == "update_product" and stock_change and not re.search(r"\b(?:price|cost)\b", lower):
        relative = re.search(rf"\bby\s+({NUMBER})", lower)
    if relative:
        amount = relative[1].replace(",", "")
        if re.match(r"(?:reduce|decrease)\b", lower) and not amount.startswith("-"):
            amount = "-" + amount.lstrip("+")
        slots = {"stock_delta": amount}
    name = re.fullmatch(r"(?:product name|product|item|name)(?:\s*[:=]\s*|\s+(?:is\s+)?)(.+)", lower)
    target = re.search(r"\b(?:product|item)\s+#?([0-9]+)\b|#([0-9]+)\b", lower)
    if target and intent in PRODUCT_LOOKUPS:
        slots["product_id"] = target[1] or target[2]
    elif name and pending != "changes":
        slots["name"] = name[1]
    elif pending == "name" and not slots and not INVENTORY_COMMAND.match(lower) and not explicit_intent(lower):
        if intent in PRODUCT_LOOKUPS and re.fullmatch(r"#?\d+", lower):
            slots["product_id"] = lower.lstrip("#")
        elif re.search(r"[a-z]", lower):
            slots["name"] = lower
    if pending in NUMBER_FIELDS and pending not in slots and not slots:
        value = re.fullmatch(rf"{CURRENCY}({NUMBER})(?:\s+(?:units?|pieces?|bags?|bottles?|cartons?|each))?", lower)
        if value:
            slots[pending] = value[1].replace(",", "")
        elif re.fullmatch(r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten)", lower):
            slots[pending] = "zero one two three four five six seven eight nine ten".split().index(lower)

    if continuing and slots and not INVENTORY_COMMAND.match(lower) and not explicit_intent(lower):
        return slots

    entities = models.inventory_bot(text).ents
    if intent in SALES and (
        len({entity.text.lower() for entity in entities if entity.label_ == "PRODUCT"}) > 1
        or re.search(rf"\band\s+{NUMBER}\s+[a-z]", lower)
    ):
        return {"multiple_items": True}
    for entity in entities:
        field = ENTITY_MAP.get(entity.label_)
        if field in {"cost_price", "selling_price"}:
            if intent == "add_product" and field == "cost_price" and not continuing:
                prefix = lower[:entity.start_char]
                amount = re.fullmatch(rf"{CURRENCY}({NUMBER})", entity.text)
                if amount and re.search(r"\bat\s*$", prefix):
                    slots.setdefault(field, amount[1].replace(",", ""))
            continue
        if field == "quantity" and (intent in PRODUCT_LOOKUPS or (continuing and pending != "quantity")):
            continue
        if field == "name" and ("product_id" in slots or pending not in {None, "name"}):
            continue
        if field and field not in slots:
            value = entity.text.strip()
            if field in NUMBER_FIELDS:
                number = re.fullmatch(rf"{CURRENCY}({NUMBER})", value)
                if number:
                    slots[field] = number[1].replace(",", "")
            else:
                slots[field] = value.lower()

    if intent in SALES and "unit_price" not in slots:
        price = re.search(rf"{CURRENCY}({NUMBER})\s*(?:each|per unit)\b", lower)
        if price:
            slots["unit_price"] = price[1].replace(",", "")
    if "name" not in slots and "product_id" not in slots and pending is None:
        product = re.fullmatch(r"(?:add|delete|remove|check|view|update)\s+(?:(?:product|item)\s+)?([a-z][\w -]*)", lower)
        if product and product[1] not in {"a product", "new product", "product", "item", "inventory", "stock"}:
            slots["name"] = product[1]
    return slots
