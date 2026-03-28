from schema.product_schema import ProductCreate
from schema.transactions_schema import TransactionCreate
from pydantic import ValidationError

# create Validation rules based on class and intent

def validator(msg_class: str, intent: str, data: dict):
    if msg_class == "inventory_conversation":
        errors = inventory_intent_validator(intent, data)
    elif msg_class == "sales_conversation":
        errors = sales_intent_validator(intent, data)
    else:
        return {
            "valid": False,
            "errors": [{"message": "Invalid class"}]
        }

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
    
def inventory_intent_validator(intent: str, data: dict):
    try:
        if intent == "add_product":
            ProductCreate(**data)

        elif intent == "increment_stock_quantity":
            if "name" not in data or "quantity" not in data:
                return [{"field": "name/quantity", "message": "Missing required fields"}]
            
        elif intent == "decrement_stock_quantity":
            if "name" not in data or "quantity" not in data:
                return [{"field": "name/quantity", "message": "Missing required fields"}]

        elif intent == "update_cost_price":
            if "name" not in data or "cost_price" not in data:
                return [{"field": "cost_price", "message": "Missing price"}]
            
        elif intent == "update_selling_price":
            if "name" not in data or "selling_price" not in data:
                return [{"field": "selling_price", "message": "Missing price"}]

        elif intent == "get_product_info":
            if "name" not in data:
                return [{"field": "name", "message": "Product name required"}]
            
        elif intent == "change_product_availabilty":
            if "name" not in data or "available" not in data:
                return [{"field": "name", "message": "Product name required"}]

        elif intent == "delete_product":
            if "name" not in data:
                return [{"field": "name", "message": "Product name required"}]

        elif intent == "view_inventory":
            return []
        
        else:
            return [{"error": "Unknown intent"}]

        return []

    except ValidationError as e:
        return parse_validation_error(e)
    

def sales_intent_validator(intent: str, data: dict):
    try:
        if intent == "record_sale" or intent == "record_purchase":

            # --- Validate items existence ---
            if "items" not in data or not isinstance(data["items"], list) or len(data["items"]) == 0:
                return [{"field": "items", "message": "At least one item is required"}]

            # --- Validate each item manually (important for good errors) ---
            for i, item in enumerate(data["items"]):
                if "product_name" not in item:
                    return [{"field": f"items[{i}].product_name", "message": "Product name required"}]

                if "quantity" not in item:
                    return [{"field": f"items[{i}].quantity", "message": "Quantity required"}]

                if "unit_price" not in item:
                    return [{"field": f"items[{i}].unit_price", "message": "Unit price required"}]

            # --- Validate full schema (final check) ---
            TransactionCreate(**data)

        elif intent == "generate_receipt":
            if "transaction_id" not in data:
                return [{"field": "transaction_id", "message": "Transaction ID required"}]

        elif intent == "get_transaction":
            if "transaction_id" not in data:
                return [{"field": "transaction_id", "message": "Transaction ID required"}]

        elif intent == "list_transactions":
            return []

        else:
            return [{"error": "Unknown intent"}]

        return []

    except ValidationError as e:
        return parse_validation_error(e)

def parse_validation_error(e: ValidationError):
    errors = []

    for err in e.errors():
        errors.append({
            "field": err["loc"][0],
            "message": err["msg"]
        })

    return errors