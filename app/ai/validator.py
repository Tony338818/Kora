from pydantic import BaseModel, ConfigDict, Field, ValidationError

from schema.product_schema import ProductCreate, ProductUpdate
from schema.transactions_schema import TransactionCreate, TransactionItemCreate


class ProductReference(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    product_id: int | None = Field(default=None, gt=0)


class TransactionReference(BaseModel):
    transaction_id: int = Field(gt=0)


class SaleItem(TransactionItemCreate):
    product_name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0, allow_inf_nan=False)


class SaleRequest(TransactionCreate):
    payment_method: str = Field(min_length=1, max_length=50)
    payment_status: str = Field(pattern="^(paid|unpaid)$")
    items: list[SaleItem] = Field(min_length=1)


class InventoryUpdate(ProductUpdate):
    model_config = ConfigDict(allow_inf_nan=False)


class StockChange(BaseModel):
    stock_delta: int = Field(ge=-2147483647, le=2147483647)


class InventoryCreate(ProductCreate):
    model_config = ConfigDict(allow_inf_nan=False)


REQUIRED_SLOTS = {
    "add_product": ["name", "quantity", "cost_price", "selling_price"],
    "update_product": ["name"],
    "get_product_info": ["name"],
    "delete_product": ["name"],
    "view_inventory": [],
    "record_sale": ["name", "quantity", "unit_price", "payment_method", "payment_status"],
    "record_purchase": ["name", "quantity", "unit_price", "payment_method", "payment_status"],
    "get_transaction": ["transaction_id"],
    "generate_receipt": ["transaction_id"],
    "list_transactions": [],
}
READ_ONLY = {"get_product_info", "view_inventory", "get_transaction", "generate_receipt", "list_transactions"}
PRODUCT_LOOKUPS = {"update_product", "get_product_info", "delete_product"}
SALES = {"record_sale", "record_purchase"}
UPDATE_FIELDS = {"new_name", "quantity", "cost_price", "selling_price", "description", "img_url", "stock_delta"}


def validate_operation(intent: str, slots: dict) -> dict:
    if intent == "add_product":
        return InventoryCreate(**slots).model_dump(exclude_unset=True)
    if intent in PRODUCT_LOOKUPS:
        target = ProductReference(**slots).model_dump(exclude_none=True)
        if intent == "update_product":
            if "stock_delta" in slots:
                return {**target, **StockChange(**slots).model_dump()}
            changes = {key: value for key, value in slots.items() if key in UPDATE_FIELDS}
            if "new_name" in changes:
                changes["name"] = changes.pop("new_name")
            target["changes"] = InventoryUpdate(**changes).model_dump(exclude_none=True)
        return target
    if intent in SALES:
        return SaleRequest(
            transaction_type=intent.removeprefix("record_"),
            items=[{**slots, "product_name": slots["name"]}],
            **slots,
        ).model_dump()
    if intent in {"get_transaction", "generate_receipt"}:
        return TransactionReference(**slots).model_dump()
    return {}


def validation_issue(error: ValidationError, intent: str) -> tuple[str, str]:
    issue = error.errors()[0]
    field = str(issue["loc"][-1])
    if field == "product_name":
        field = "name"
    elif field == "name" and intent == "update_product":
        # Update values use a distinct slot from the lookup name.
        field = "new_name" if error.title == "InventoryUpdate" else "name"
    return field, issue["msg"]
