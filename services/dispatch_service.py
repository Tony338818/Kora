from services.inventory_service import (
    add_product, increment_stock, decrement_stock,
    update_cost_price, update_selling_price,
    get_product_info, delete_product, view_inventory
)
from services.transaction_service import (
    record_sale, record_purchase, get_transaction,
    list_transactions, generate_receipt
)

HANDLERS = {
    # ── inventory ──────────────────────────────
    "add_product":              add_product,
    "increment_stock_quantity": increment_stock,
    "decrement_stock_quantity": decrement_stock,
    "update_cost_price":        update_cost_price,
    "update_selling_price":     update_selling_price,
    "get_product_info":         get_product_info,
    "delete_product":           delete_product,
    "view_inventory":           view_inventory,
 
    # ── sales ──────────────────────────────────
    "record_sale":              record_sale,
    "record_purchase":          record_purchase,
    "get_transaction":          get_transaction,
    "list_transactions":        list_transactions,
    "generate_receipt":         generate_receipt,
}

def dispatch(db, phone: str, intent: str, data: dict) -> str:
    handler = HANDLERS.get(intent)
    if not handler:
        return "Unknown intent."
    return handler(db, phone, data)