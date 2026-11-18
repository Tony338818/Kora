from schema.db_schema import Products
from services.inventory_service import InventoryService
from services.receipt_service import ReceiptService
from services.sales_service import SalesService
from services.transaction_service import TransactionService


def dispatch(db, user_id: int, intent: str, data: dict):
    inventory = InventoryService(db, user_id)

    if intent == "add_product":
        return inventory.create_product(data)
    if intent == "view_inventory":
        return inventory.read_all_products()
    if intent in {"get_product_info", "update_product", "delete_product"}:
        name = data.get("name")
        if "product_id" in data:
            product_id = data["product_id"]
            product = db.query(Products).filter_by(id=product_id, user_id=user_id).first()
            if product is None:
                return {"success": False, "message": f"Product #{product_id} was not found."}
            name = product.name

        if intent == "get_product_info":
            return inventory.read_product(name)
        if intent == "update_product":
            if "stock_delta" in data:
                return inventory.adjust_stock(name, data["stock_delta"])
            return inventory.update_product(name, data["changes"])
        return inventory.delete_product(name)

    if intent == "record_sale":
        return SalesService(db, user_id).record_sale(data)
    if intent == "record_purchase":
        return SalesService(db, user_id).record_purchase(data)
    if intent == "get_transaction":
        return TransactionService(db, user_id).get_transaction(data["transaction_id"])
    if intent == "list_transactions":
        return TransactionService(db, user_id).list_transactions()
    if intent == "generate_receipt":
        return ReceiptService(db, user_id).generate_receipt(data["transaction_id"])
    return {"success": False, "message": "I don't support that operation yet."}
