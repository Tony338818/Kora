# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# from schema.db_schema import Products, Users
# from schema.product_schema import ProductCreate, ProductUpdate

# class InventoryService:
#     def createProduct(db: Session, product_data: ProductCreate, current_user_id:int):
#         new_product = Products(
#             user_id = current_user_id,
#             **product_data.model_dump(exclude_unset=False)
#         )
        
#         try:
#             db.add(new_product)
#             db.commit()
#             db.refresh(new_product)
#             return {
#                 'success': True,
#                 'product': new_product,
#                 'message': 'Product added successfully'
#             }
#         except Exception as e:
#             db.rollback()
#             return {
#                 'success': False,
#                 'product': None,
#                 'message': 'Failed to add product please try again'
#             }
            
#     def readProducts(db: Session, current_user_id:int):
#         # user = db.get(Users, current_user_id)
#         # if not user:
#         #     return {
#         #         'success': False,
#         #         'data': [],
#         #         'message': 'User not found!'
#         #     }
            
#         results = db.query(Products).filter_by(user_id = current_user_id)
#         if not results:
#             return {
#                 'success': True,
#                 'product': None,
#                 'message': 'No products Found'
#             }
        
#         products = [
#             {
#                 'id': product.id,
#                 'name' : product.name,
#                 'quantity' : product.quantity,
#                 'cost_price' : product.cost_price,
#                 'selling_price' : product.selling_price,
#                 'supplier' : product.supplier,
#                 'img_url' : product.img_url,
#                 'description' : product.description,
#                 'buy_date' : product.buy_date,
#                 'expiry_date' : product.expiry_date
#             } for product in results
#         ]
#         return {
#                 'success': True,
#                 'product': products,
#                 'message': 'Products retrieved'
#             }
        
#     def readProductByID(db: Session,current_user_id:int, product_id: int):
#         try:
#             results = db.query(Products).filter_by(user_id = current_user_id)
#             if not results:
#                 return {
#                     'success': True,
#                     'product': None,
#                     'message': 'No products Found'
#                 }
#             result = db.get(Products, product_id)
#             if not result:
#                 return 'Data does not exist in the DB'
            
#             return result
#         except Exception as e:
#             return e
#     def updateProduct(db: Session, current_user_id: int, product_id:int, data: ProductUpdate):
#         try:
#             results = db.query(Products).filter_by(user_id = current_user_id).all()
#             if not results:
#                 return {
#                     'success': True,
#                     'product': None,
#                     'message': 'You do not have any products in the database'
#                 }
                
#             if not any(product_id == result.id for result in results):
#                 return {
#                     'success': False,
#                     'product': None,
#                     'message': 'You cannot edit a product not tied to your account'
#                 }
                
#             product = db.get(Products, product_id)
#             if not product:
#                 return {
#                     'success': False,
#                     'product': None,
#                     'message': 'No products Found'
#                 }
            
#             for key, value in data.model_dump(exclude_unset=True).items():
#                 setattr(product, key, value)
                
#             db.commit()
#             return {
#                 'success': True,
#                 'product': product,
#                 'message':'Product detail Updated Successfully'
#                 }
#         except Exception as e:
#             return {
#                 'success': False,
#                 'product': None,
#                 'message':f'{e}'
#                 }
#     def deleteProduct(db: Session, current_user_id: int, product_id: int):
#         try:
#             results = db.query(Products).filter_by(user_id = current_user_id).all()
#             if not results:
#                 return {
#                     'success': False,
#                     'product': None,
#                     'message': 'You do not have any products in the database'
#                 }
                
#             if not any(product_id == result.id for result in results):
#                 return {
#                     'success': False,
#                     'product': None,
#                     'message': 'You cannot delete a product not tied to your account'
#                 }
                
#             product = db.get(Products, product_id)
           
#             if not product:
#                 return {
#                     'success': False,
#                     'product': None,
#                     'message': 'You cannot delete a product not tied to your account'
#                 }
           
#             db.delete(product)
#             db.commit()
#             return {
#                 'success': True,
#                 'product': product,
#                 'message': 'product deleted successfully'
#             }
#         except Exception as e:
#              return {
#                 'success': False,
#                 'product': None,
#                 'message': f'{e}'
#             }
             
             
             
# # Inventory services
# # add_product 
# # increment_stock
# def increment_stock_qty(db: Session, current_user_id: int, product_name:int, data: ProductUpdate):
#     products = db.query(Products).filter_by(user_id = current_user_id)
#     if not products:
#         return {
#         'success': True,
#         'product': None,
#         'message': 'You do not have any products in the database'
#                 }




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

def add_product(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    # Check for duplicate
    existing = get_product_by_name(db, user.id, data.get("name", ""))
    if existing:
        return f"Product '{data['name']}' already exists. Did you mean to update stock?"

    try:
        product_data = ProductCreate(**data)
        new_product = Products(
            user_id=user.id,
            **product_data.model_dump(exclude_unset=False)
        )
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return f"'{new_product.name}' added successfully with {new_product.quantity} units."
    except Exception as e:
        db.rollback()
        return f"Failed to add product: {e}"


# ─── 2. increment_stock ───────────────────────────────────────────────────────

def increment_stock(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    name = data.get("name")
    quantity = data.get("quantity")

    product = get_product_by_name(db, user.id, name)
    if not product:
        return f"Product '{name}' not found in your inventory."

    try:
        product.quantity += quantity
        db.commit()
        return f"Stock updated. '{product.name}' now has {product.quantity} units."
    except Exception as e:
        db.rollback()
        return f"Failed to update stock: {e}"


# ─── 3. decrement_stock ───────────────────────────────────────────────────────

def decrement_stock(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    name = data.get("name")
    quantity = data.get("quantity")

    product = get_product_by_name(db, user.id, name)
    if not product:
        return f"Product '{name}' not found in your inventory."

    if product.quantity - quantity < 0:
        return (
            f"Cannot remove {quantity} units. "
            f"'{product.name}' only has {product.quantity} units in stock."
        )

    try:
        product.quantity -= quantity
        db.commit()
        return f"Stock updated. '{product.name}' now has {product.quantity} units."
    except Exception as e:
        db.rollback()
        return f"Failed to update stock: {e}"


# ─── 4. update_cost_price ─────────────────────────────────────────────────────

def update_cost_price(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    name = data.get("name")
    cost_price = data.get("cost_price")

    product = get_product_by_name(db, user.id, name)
    if not product:
        return f"Product '{name}' not found in your inventory."

    try:
        product.cost_price = cost_price
        db.commit()
        return f"Cost price for '{product.name}' updated to {cost_price}."
    except Exception as e:
        db.rollback()
        return f"Failed to update cost price: {e}"


# ─── 5. update_selling_price ──────────────────────────────────────────────────

def update_selling_price(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    name = data.get("name")
    selling_price = data.get("selling_price")

    product = get_product_by_name(db, user.id, name)
    if not product:
        return f"Product '{name}' not found in your inventory."

    try:
        product.selling_price = selling_price
        db.commit()
        return f"Selling price for '{product.name}' updated to {selling_price}."
    except Exception as e:
        db.rollback()
        return f"Failed to update selling price: {e}"


# ─── 6. get_product_info ──────────────────────────────────────────────────────

def get_product_info(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    name = data.get("name")

    product = get_product_by_name(db, user.id, name)
    if not product:
        return f"Product '{name}' not found in your inventory."

    return (
        f" {product.name.title()}\n"
        f"  Quantity     : {product.quantity}\n"
        f"  Cost Price   : {product.cost_price}\n"
        f"  Selling Price: {product.selling_price}\n"
        f"  Supplier     : {product.supplier or 'N/A'}\n"
        f"  Expiry Date  : {product.expiry_date or 'N/A'}"
    )


# ─── 7. delete_product ────────────────────────────────────────────────────────

def delete_product(db: Session, phone: str, data: dict) -> str:
    user = get_user(db, phone)
    if not user:
        return "User not found."

    name = data.get("name")

    product = get_product_by_name(db, user.id, name)
    if not product:
        return f"Product '{name}' not found in your inventory."

    try:
        db.delete(product)
        db.commit()
        return f"✅ '{name}' has been deleted from your inventory."
    except Exception as e:
        db.rollback()
        return f"Failed to delete product: {e}"


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