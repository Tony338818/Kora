ENTITY_MAP = {
    "PRODUCT": "name",
    "QUANTITY": "quantity",
    "UNIT": "unit",
    "COST_PRICE": "cost_price",
    "SELL_PRICE": "selling_price",
    "CUSTOMER": "customer",
    "SUPPLIER": "supplier",
}


def normalize_inventory_entities(entities: dict) -> dict:
    normalized = {}

    for key, value in entities.items():
        canonical_key = ENTITY_MAP.get(key)

        # Ignore entities this domain doesn't understand
        if canonical_key is None:
            continue

        normalized[canonical_key] = value

    # Normalize types
    if "quantity" in normalized:
        normalized["quantity"] = int(normalized["quantity"])

    if "cost_price" in normalized:
        normalized["cost_price"] = float(normalized["cost_price"])

    if "selling_price" in normalized:
        normalized["selling_price"] = float(normalized["selling_price"])

    return normalized