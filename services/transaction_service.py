# from sqlalchemy.orm import Session
# from schema.db_schema import Transactions, TransactionItem, Products
# from schema.transactions_schema import TransactionCreate


# class TransactionService:

#     def createTransaction(db: Session, transaction_data: TransactionCreate, current_user_id: int):

#         try:
#             total_amount = 0
#             items_list = []

#             for item in transaction_data.items:

#                 subtotal = item.quantity * item.unit_price
#                 total_amount += subtotal

#                 new_item = TransactionItem(
#                     product_id=item.product_id,
#                     product_name=item.product_name,
#                     quantity=item.quantity,
#                     unit_price=item.unit_price,
#                     subtotal=subtotal
#                 )

#                 items_list.append(new_item)

#             new_transaction = Transactions(
#                 user_id=current_user_id,
#                 amount=total_amount,
#                 transaction_type=transaction_data.transaction_type,
#                 payment_method=transaction_data.payment_method,
#                 payment_status=transaction_data.payment_status,
#                 items=items_list
#             )

#             db.add(new_transaction)
#             db.commit()
#             db.refresh(new_transaction)

#             return {
#                 "success": True,
#                 "transaction": new_transaction,
#                 "message": "Transaction created successfully"
#             }

#         except Exception as e:
#             db.rollback()
#             return {
#                 "success": False,
#                 "transaction": None,
#                 "message": f"{e}"
#             }

#     def readTransactions(db: Session, current_user_id: int):

#         results = db.query(Transactions).filter_by(user_id=current_user_id).all()

#         if not results:
#             return {
#                 "success": True,
#                 "transaction": None,
#                 "message": "No transactions found"
#             }

#         return {
#             "success": True,
#             "transaction": results,
#             "message": "Transactions retrieved"
#         }

#     def readTransactionByID(db: Session, current_user_id: int, transaction_id: int):

#         try:
#             results = db.query(Transactions).filter_by(user_id=current_user_id).all()

#             if not results:
#                 return {
#                     "success": True,
#                     "transaction": None,
#                     "message": "You do not have any transactions"
#                 }

#             if not any(transaction_id == result.id for result in results):
#                 return {
#                     "success": False,
#                     "transaction": None,
#                     "message": "You cannot access a transaction not tied to your account"
#                 }

#             transaction = db.get(Transactions, transaction_id)

#             if not transaction:
#                 return {
#                     "success": False,
#                     "transaction": None,
#                     "message": "Transaction not found"
#                 }

#             return {
#                 "success": True,
#                 "transaction": transaction,
#                 "message": "Transaction retrieved"
#             }

#         except Exception as e:
#             return {
#                 "success": False,
#                 "transaction": None,
#                 "message": f"{e}"
#             }

#     def deleteTransaction(db: Session, current_user_id: int, transaction_id: int):

#         try:
#             results = db.query(Transactions).filter_by(user_id=current_user_id).all()

#             if not results:
#                 return {
#                     "success": False,
#                     "transaction": None,
#                     "message": "You do not have any transactions"
#                 }

#             if not any(transaction_id == result.id for result in results):
#                 return {
#                     "success": False,
#                     "transaction": None,
#                     "message": "You cannot delete a transaction not tied to your account"
#                 }

#             transaction = db.get(Transactions, transaction_id)

#             if not transaction:
#                 return {
#                     "success": False,
#                     "transaction": None,
#                     "message": "Transaction not found"
#                 }

#             db.delete(transaction)
#             db.commit()

#             return {
#                 "success": True,
#                 "transaction": transaction,
#                 "message": "Transaction deleted successfully"
#             }

#         except Exception as e:
#             return {
#                 "success": False,
#                 "transaction": None,
#                 "message": f"{e}"
#             }



from sqlalchemy.orm import Session
from schema.db_schema import Transactions, TransactionItem, Products, Users
from schema.transactions_schema import TransactionCreate, TransactionItemCreate


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_user(db: Session, phone: str):
    """Resolve whatsapp:+234... to a DB user."""
    return db.query(Users).filter_by(phone_number=phone).first()


def resolve_product_id(db: Session, user_id: int, product_name: str) -> int | None:
    """Look up a product by name and return its ID."""
    product = (
        db.query(Products)
        .filter_by(user_id=user_id, name=product_name.lower())
        .first()
    )
    return product.id if product else None


def format_transaction(t: Transactions) -> str:
    """Format a transaction object into a readable string."""
    lines = [
        f"Transaction #{t.id}",
        f"  Type           : {t.transaction_type}",
        f"  Amount         : {t.amount}",
        f"  Payment Method : {t.payment_method or 'N/A'}",
        f"  Payment Status : {t.payment_status or 'N/A'}",
        f"  Date           : {t.created_at if hasattr(t, 'created_at') else 'N/A'}",
        f"  Items:",
    ]
    for item in t.items:
        lines.append(
            f"    • {item.product_name} x{item.quantity} @ {item.unit_price} = {item.subtotal}"
        )
    return "\n".join(lines)


# ─── 1. record_sale ───────────────────────────────────────────────────────────

def record_sale(db: Session, phone: str, data: dict) -> str:
    return create_transaction(db, phone, data, transaction_type="sale")


# ─── 2. record_purchase ───────────────────────────────────────────────────────

def record_purchase(db: Session, phone: str, data: dict) -> str:
    return create_transaction(db, phone, data, transaction_type="purchase")


# ─── Shared transaction creator ───────────────────────────────────────────────

def create_transaction(db: Session, phone: str, data: dict, transaction_type: str) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    items_data = data.get("items", [])
    if not items_data:
        return "No items provided for this transaction."

    try:
        total_amount = 0
        items_list = []

        for item in items_data:
            product_name = item.get("product_name", "")
            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", 0)
            subtotal = quantity * unit_price
            total_amount += subtotal

            # resolve product_id from name — None if product not in inventory
            product_id = resolve_product_id(db, user.id, product_name)

            items_list.append(TransactionItem(
                product_id=product_id,
                product_name=product_name.lower(),
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal
            ))

        new_transaction = Transactions(
            user_id=user.id,
            amount=total_amount,
            transaction_type=transaction_type,
            payment_method=data.get("payment_method"),
            payment_status=data.get("payment_status", "paid"),
            items=items_list
        )

        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

        # build summary
        item_lines = "\n".join(
            f"  • {i.product_name} x{i.quantity} @ {i.unit_price}"
            for i in new_transaction.items
        )
        return (
            f"✅ {transaction_type.title()} recorded successfully.\n"
            f"{item_lines}\n"
            f"  Total: {new_transaction.amount}\n"
            f"  Payment: {new_transaction.payment_method or 'N/A'} — {new_transaction.payment_status}"
        )

    except Exception as e:
        db.rollback()
        return f"Failed to record {transaction_type}: {e}"


# ─── 3. get_transaction ───────────────────────────────────────────────────────

def get_transaction(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    transaction_id = data.get("transaction_id")
    if not transaction_id:
        return "Transaction ID is required."

    # verify ownership
    user_transactions = db.query(Transactions).filter_by(user_id=user.id).all()
    if not any(t.id == transaction_id for t in user_transactions):
        return "Transaction not found on your account."

    transaction = db.get(Transactions, transaction_id)
    if not transaction:
        return "Transaction not found."

    return format_transaction(transaction)


# ─── 4. list_transactions ─────────────────────────────────────────────────────

def list_transactions(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    transactions = db.query(Transactions).filter_by(user_id=user.id).all()
    if not transactions:
        return "You have no transactions yet."

    lines = [f"📋 Your Transactions ({len(transactions)} total):\n"]
    for t in transactions:
        lines.append(
            f"  #{t.id} | {t.transaction_type.title()} | "
            f"Amount: {t.amount} | Status: {t.payment_status or 'N/A'}"
        )

    return "\n".join(lines)


# ─── 5. generate_receipt ──────────────────────────────────────────────────────

def generate_receipt(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    transaction_id = data.get("transaction_id")
    if not transaction_id:
        return "Transaction ID is required to generate a receipt."

    # verify ownership
    user_transactions = db.query(Transactions).filter_by(user_id=user.id).all()
    if not any(t.id == transaction_id for t in user_transactions):
        return "Transaction not found on your account."

    t = db.get(Transactions, transaction_id)
    if not t:
        return "Transaction not found."

    divider = "─" * 32
    lines = [
        divider,
        "         RECEIPT",
        divider,
        f"Transaction ID : #{t.id}",
        f"Type           : {t.transaction_type.title()}",
        f"Payment Method : {t.payment_method or 'N/A'}",
        f"Payment Status : {t.payment_status or 'N/A'}",
        divider,
        "Items:",
    ]

    for item in t.items:
        lines.append(f"  {item.product_name.title()}")
        lines.append(f"    {item.quantity} x {item.unit_price} = {item.subtotal}")

    lines += [
        divider,
        f"TOTAL          : {t.amount}",
        divider,
    ]

    return "\n".join(lines)