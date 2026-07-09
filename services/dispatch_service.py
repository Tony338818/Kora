from services.inventory_service import InventoryService
from services.transaction_service import (
    record_sale, record_purchase, get_transaction,
    list_transactions, generate_receipt
)

def dispatch(db, phone: str, intent: str, data: dict):
    inventory = InventoryService(db, phone)

    if intent == "add_product":
        return inventory.create_product(data)

    elif intent == "view_inventory":
        return inventory.read_all_product()

    elif intent == "get_product_info":
        return inventory.read_product(data["product_id"])

    elif intent == "update_product":
        product_id = data.pop("product_id")
        return inventory.update_product(product_id, data)

    elif intent == "delete_product":
        return inventory.delete_product(data["product_id"])