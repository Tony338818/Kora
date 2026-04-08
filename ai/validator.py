from schema.product_schema import ProductCreate
from schema.transactions_schema import TransactionCreate
from pydantic import ValidationError

# create Validation rules based on class and intent

def validator(msg_class: str, intent: str, data: dict):
    if msg_class == "inventory_conversation":
        result = inventory_intent_validator(intent, data)
    elif msg_class == "sales_conversation":
        result = sales_intent_validator(intent, data)
    else:
        return {
            "valid": False,
            "message": "Invalid request type"
        }

    return result
    
def inventory_intent_validator(intent: str, data: dict):
    try:
        if intent == "add_product":
            ProductCreate(**data)
            return {"valid": True}

        elif intent in ["increment_stock_quantity", "decrement_stock_quantity"]:
            name = data.get("name")
            quantity = data.get("quantity")

            if not name and not quantity:
                return {"valid": False, "message": "Please provide the product name and quantity."}
            elif not name:
                return {"valid": False, "message": "Which product are you referring to?"}
            elif not quantity:
                return {"valid": False, "message": "How many units should I update?"}

            return {"valid": True}

        elif intent == "update_cost_price":
            name = data.get("name")
            price = data.get("cost_price")

            if not name and not price:
                return {"valid": False, "message": "Please provide the product name and cost price."}
            elif not name:
                return {"valid": False, "message": "Which product do you want to update?"}
            elif not price:
                return {"valid": False, "message": "What is the new cost price?"}

            return {"valid": True}

        elif intent == "update_selling_price":
            name = data.get("name")
            price = data.get("selling_price")

            if not name and not price:
                return {"valid": False, "message": "Please provide the product name and selling price."}
            elif not name:
                return {"valid": False, "message": "Which product do you want to update?"}
            elif not price:
                return {"valid": False, "message": "What is the new selling price?"}

            return {"valid": True}

        elif intent == "get_product_info":
            if not data.get("name"):
                return {"valid": False, "message": "Which product do you want information about?"}
            return {"valid": True}

        elif intent == "change_product_availabilty":
            name = data.get("name")
            available = data.get("available")

            if not name and available is None:
                return {"valid": False, "message": "Please provide the product name and availability status."}
            elif not name:
                return {"valid": False, "message": "Which product are you updating?"}
            elif available is None:
                return {"valid": False, "message": "Should the product be available or unavailable?"}

            return {"valid": True}

        elif intent == "delete_product":
            if not data.get("name"):
                return {"valid": False, "message": "Which product do you want to delete?"}
            return {"valid": True}

        elif intent == "view_inventory":
            return {"valid": True}

        else:
            return {"valid": False, "message": "Unknown inventory action"}

    except ValidationError as e:
        return {
            "valid": False,
            "message": parse_validation_error_message(e)
        }
    

def sales_intent_validator(intent: str, data: dict):
    try:
        if intent in ["record_sale", "record_purchase"]:

            items = data.get("items")

            if not items:
                return {"valid": False, "message": "What items are you recording?"}

            item = items[0]  # keep simple for now

            name = item.get("product_name")
            quantity = item.get("quantity")
            price = item.get("unit_price")

            if not name and not quantity and not price:
                return {"valid": False, "message": "Please provide product name, quantity, and price."}
            elif not name:
                return {"valid": False, "message": "Which product was involved?"}
            elif not quantity:
                return {"valid": False, "message": "How many units were involved?"}
            elif not price:
                return {"valid": False, "message": "What price was it sold for?"}

            TransactionCreate(**data)
            return {"valid": True}

        elif intent in ["generate_receipt", "get_transaction"]:
            if not data.get("transaction_id"):
                return {"valid": False, "message": "Please provide the transaction ID."}
            return {"valid": True}

        elif intent == "list_transactions":
            return {"valid": True}

        else:
            return {"valid": False, "message": "Unknown sales action"}

    except ValidationError as e:
        return {
            "valid": False,
            "message": parse_validation_error_message(e)
        }

def parse_validation_error_message(e: ValidationError):
    first_error = e.errors()[0]
    field = first_error["loc"][0]
    msg = first_error["msg"]

    return f"{field.replace('_', ' ').capitalize()} error: {msg}"