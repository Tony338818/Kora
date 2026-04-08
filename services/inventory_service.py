from sqlalchemy.orm import Session
from schema.db_schema import Products, Users
from schema.product_schema import ProductCreate, ProductUpdate


# ─── Helper ───────────────────────────────────────────────────────────────────

def get_user(db: Session, phone: str):
    """Resolve whatsapp:+234... string to a DB user."""
    return db.query(Users).filter_by(phone_number=phone).first()


def get_product_by_name(db: Session, current_user_id: int, name: str):
    """Fetch a product by name for a specific user."""
    return (
        db.query(Products)
        .filter_by(user_id=current_user_id, name=name.lower())
        .first()
    )


# ─── 1. add_product ───────────────────────────────────────────────────────────

def add_product(db: Session, phone: str, data: dict):
    user = get_user(db, phone)
    if not user:
        return {"success": False, "message": "User not found."}

    existing = get_product_by_name(db, user.id, data.get("name", ""))
    if existing:
        return {
            "success": False,
            "message": f"Product '{data['name']}' already exists. Did you mean to update stock?"
        }

    try:
        product_data = ProductCreate(**data)
        new_product = Products(
            user_id=user.id,
            **product_data.model_dump(exclude_unset=False)
        )

        db.add(new_product)
        db.commit()
        db.refresh(new_product)

        return {
            "success": True,
            "message": f"'{new_product.name}' added successfully with {new_product.quantity} units.",
            "data": {"product_id": new_product.id}
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Failed to add product: {e}"}


# ─── 2. increment_stock ───────────────────────────────────────────────────────

def increment_stock(db: Session, phone: str, data: dict):
    user = get_user(db, phone)
    if not user:
        return {"success": False, "message": "User not found."}

    product = get_product_by_name(db, user.id, data.get("name"))

    if not product:
        return {
            "success": False,
            "message": f"Product '{data.get('name')}' not found in your inventory."
        }

    try:
        product.quantity += data.get("quantity")
        db.commit()

        return {
            "success": True,
            "message": f"Stock updated. '{product.name}' now has {product.quantity} units.",
            "data": {"quantity": product.quantity}
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Failed to update stock: {e}"}


# ─── 3. decrement_stock ───────────────────────────────────────────────────────

def decrement_stock(db: Session, phone: str, data: dict):
    user = get_user(db, phone)
    if not user:
        return {"success": False, "message": "User not found."}

    product = get_product_by_name(db, user.id, data.get("name"))

    if not product:
        return {
            "success": False,
            "message": f"Product '{data.get('name')}' not found in your inventory."
        }

    if product.quantity < data.get("quantity"):
        return {
            "success": False,
            "message": f"Cannot remove {data.get('quantity')} units. Only {product.quantity} available."
        }

    try:
        product.quantity -= data.get("quantity")
        db.commit()

        return {
            "success": True,
            "message": f"Stock updated. '{product.name}' now has {product.quantity} units.",
            "data": {"quantity": product.quantity}
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Failed to update stock: {e}"}


# ─── 4. update_cost_price ─────────────────────────────────────────────────────

def update_cost_price(db: Session, phone: str, data: dict):
    user = get_user(db, phone)
    if not user:
        return {"success": False, "message": "User not found."}

    product = get_product_by_name(db, user.id, data.get("name"))

    if not product:
        return {
            "success": False,
            "message": f"Product '{data.get('name')}' not found."
        }

    try:
        product.cost_price = data.get("cost_price")
        db.commit()

        return {
            "success": True,
            "message": f"Cost price updated to {product.cost_price}.",
            "data": {"cost_price": product.cost_price}
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Failed: {e}"}


# ─── 5. update_selling_price ──────────────────────────────────────────────────

def update_selling_price(db: Session, phone: str, data: dict):
    user = get_user(db, phone)
    if not user:
        return {"success": False, "message": "User not found."}

    product = get_product_by_name(db, user.id, data.get("name"))

    if not product:
        return {
            "success": False,
            "message": f"Product '{data.get('name')}' not found."
        }

    try:
        product.selling_price = data.get("selling_price")
        db.commit()

        return {
            "success": True,
            "message": f"Selling price updated to {product.selling_price}.",
            "data": {"selling_price": product.selling_price}
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Failed: {e}"}


# ─── 6. get_product_info ──────────────────────────────────────────────────────

def get_product_info(db: Session, phone: str, data: dict):
    user = get_user(db, phone)
    if not user:
        return {"success": False, "message": "User not found."}

    product = get_product_by_name(db, user.id, data.get("name"))

    if not product:
        return {
            "success": False,
            "message": f"Product '{data.get('name')}' not found."
        }

    return {
        "success": True,
        "message": f"{product.name} details retrieved.",
        "data": {
            "name": product.name,
            "quantity": product.quantity,
            "cost_price": product.cost_price,
            "selling_price": product.selling_price,
            "supplier": product.supplier,
            "expiry_date": product.expiry_date
        }
    }


# ─── 7. delete_product ────────────────────────────────────────────────────────

def delete_product(db: Session, phone: str, data: dict):
    user = get_user(db, phone)
    if not user:
        return {"success": False, "message": "User not found."}

    product = get_product_by_name(db, user.id, data.get("name"))

    if not product:
        return {
            "success": False,
            "message": f"Product '{data.get('name')}' not found."
        }

    try:
        db.delete(product)
        db.commit()

        return {
            "success": True,
            "message": f"'{product.name}' deleted successfully."
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"Failed: {e}"}


# ─── 8. view_inventory ────────────────────────────────────────────────────────

def view_inventory(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    products = db.query(Products).filter_by(user_id=user.id).all()
    if not products:
        return "Your inventory is empty."

    lines = ["Your Inventory:\n"]
    for p in products:
        lines.append(
            f"  • {p.name.title()}: {p.quantity} units @ {p.selling_price} each"
        )

    return "\n".join(lines)