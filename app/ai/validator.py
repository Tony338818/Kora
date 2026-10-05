from pydantic import ValidationError

from schema.product_schema import ProductCreate
from schema.transactions_schema import TransactionCreate


def validator(msg_class: str, intent: str, data: dict):
    """
    Validate whether the current task contains enough information
    to execute the requested action.
    """

    if msg_class == "inventory":
        return inventory_intent_validator(intent, data)

    if msg_class == "sales_conversation":
        return sales_intent_validator(intent, data)

    return {
        "valid": False,
        "missing_fields": [],
        "message": "Invalid request type",
    }


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def is_missing(value) -> bool:
    """
    A value is considered missing only when it is None
    or an empty string.

    This avoids treating values such as 0 or False as missing.
    """

    return value is None or (
        isinstance(value, str) and not value.strip()
    )


def get_missing_fields_from_validation_error(
    error: ValidationError
) -> list[str]:
    """
    Extract fields that Pydantic reports as missing.
    """

    missing_fields = []

    for validation_error in error.errors():

        if validation_error["type"] == "missing":
            location = validation_error["loc"]

            if location:
                field = str(location[-1])

                if field not in missing_fields:
                    missing_fields.append(field)

    return missing_fields


def parse_validation_error_message(error: ValidationError) -> str:
    """
    Convert the first non-missing Pydantic validation error
    into a readable message.
    """

    first_error = error.errors()[0]

    location = first_error["loc"]
    field = str(location[-1]) if location else "value"

    message = first_error["msg"]

    return (
        f"{field.replace('_', ' ').capitalize()} "
        f"error: {message}"
    )


# ---------------------------------------------------------
# Inventory
# ---------------------------------------------------------

def inventory_intent_validator(intent: str, data: dict):

    if intent == "add_product":
        try:
            ProductCreate(**data)

            return {
                "valid": True,
                "missing_fields": [],
            }

        except ValidationError as error:

            missing_fields = (
                get_missing_fields_from_validation_error(error)
            )

            if missing_fields:
                return {
                    "valid": False,
                    "missing_fields": missing_fields,
                }

            # Data exists but one of the values is invalid
            return {
                "valid": False,
                "missing_fields": [],
                "message": parse_validation_error_message(error),
            }

    elif intent in [
        "increment_stock_quantity",
        "decrement_stock_quantity",
    ]:
        missing_fields = []

        if is_missing(data.get("name")):
            missing_fields.append("name")

        if is_missing(data.get("quantity")):
            missing_fields.append("quantity")

        return {
            "valid": not missing_fields,
            "missing_fields": missing_fields,
        }

    elif intent == "update_cost_price":
        missing_fields = []

        if is_missing(data.get("name")):
            missing_fields.append("name")

        if is_missing(data.get("cost_price")):
            missing_fields.append("cost_price")

        return {
            "valid": not missing_fields,
            "missing_fields": missing_fields,
        }

    elif intent == "update_selling_price":
        missing_fields = []

        if is_missing(data.get("name")):
            missing_fields.append("name")

        if is_missing(data.get("selling_price")):
            missing_fields.append("selling_price")

        return {
            "valid": not missing_fields,
            "missing_fields": missing_fields,
        }

    elif intent == "get_product_info":
        missing_fields = []

        if is_missing(data.get("name")):
            missing_fields.append("name")

        return {
            "valid": not missing_fields,
            "missing_fields": missing_fields,
        }

    elif intent == "change_product_availabilty":
        missing_fields = []

        if is_missing(data.get("name")):
            missing_fields.append("name")

        # False is a valid value here
        if data.get("available") is None:
            missing_fields.append("available")

        return {
            "valid": not missing_fields,
            "missing_fields": missing_fields,
        }

    elif intent == "delete_product":
        missing_fields = []

        if is_missing(data.get("name")):
            missing_fields.append("name")

        return {
            "valid": not missing_fields,
            "missing_fields": missing_fields,
        }

    elif intent == "view_inventory":
        return {
            "valid": True,
            "missing_fields": [],
        }

    return {
        "valid": False,
        "missing_fields": [],
        "message": "Unknown inventory action",
    }


# ---------------------------------------------------------
# Sales
# ---------------------------------------------------------

def sales_intent_validator(intent: str, data: dict):

    if intent in ["record_sale", "record_purchase"]:

        items = data.get("items")

        if not items:
            return {
                "valid": False,
                "missing_fields": ["items"],
            }

        # Single item for the alpha
        item = items[0]

        missing_fields = []

        if is_missing(item.get("product_name")):
            missing_fields.append("product_name")

        if is_missing(item.get("quantity")):
            missing_fields.append("quantity")

        if is_missing(item.get("unit_price")):
            missing_fields.append("unit_price")

        if missing_fields:
            return {
                "valid": False,
                "missing_fields": missing_fields,
            }

        try:
            TransactionCreate(**data)

            return {
                "valid": True,
                "missing_fields": [],
            }

        except ValidationError as error:

            missing = get_missing_fields_from_validation_error(
                error
            )

            if missing:
                return {
                    "valid": False,
                    "missing_fields": missing,
                }

            return {
                "valid": False,
                "missing_fields": [],
                "message": parse_validation_error_message(error),
            }

    elif intent in [
        "generate_receipt",
        "get_transaction",
    ]:
        missing_fields = []

        if is_missing(data.get("transaction_id")):
            missing_fields.append("transaction_id")

        return {
            "valid": not missing_fields,
            "missing_fields": missing_fields,
        }

    elif intent == "list_transactions":
        return {
            "valid": True,
            "missing_fields": [],
        }

    return {
        "valid": False,
        "missing_fields": [],
        "message": "Unknown sales action",
    }