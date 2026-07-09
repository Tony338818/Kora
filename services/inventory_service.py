from sqlalchemy.orm import Session
from schema.db_schema import Products, Users
from schema.product_schema import ProductCreate


class InventoryService:
    def __int__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        
    # Helper Method
    def get_product_by_name(self, name: str):
        """Fetch a product by name for a specific user."""
        return (
            self.db.query(Products)
            .filter_by(user_id=self.user_id, name=name.lower())
            .first()
        )
        
    def _get_product(self, product_id: str) -> Products:
        product = (
            self.db.query(Products)
            .filter_by(
                id=product_id,
                user_id=self.user_id
            )
            .first()
        )

        if product is None:
            raise     

        return product
    # Create product for a specific user in the database 
    def create_product(self, data: dict):
        """Creates a product in the db and links it to a specific user"""
        try:
            product_data = ProductCreate(**data)
            new_product = Products(
                user_id=self.user_id,
                **product_data.model_dump(exclude_unset=False)
            )

            self.db.add(new_product)
            self.db.commit()
            self.db.refresh(new_product)

            return {
                "success": True,
                "message": f"'{new_product.name}' added successfully with {new_product.quantity} units.",
                "data": {"product_id": new_product.id}
            }

        except Exception as e:
            self.db.rollback()
            return {"success": False, "message": f"Failed to add product: {e}"}
        
    # Read products belonging to a single user from the database
    # Read all products belonging to that user from the db.
    def read_all_product(self):
        products = self.db.query(Products).filter_by(user_id=self.user_id).all()
        if not products:
            return "Your inventory is empty."

        lines = ["Your Inventory:\n"]
        for p in products:
            lines.append(
                f"  • {p.name.title()}: {p.quantity} units @ {p.selling_price} each"
            )

        return "\n".join(lines)
    
    # Read product by ID
    def read_product(self, product_id: str):
        product = self.db.query(Products).filter_by(user_id=self.user_id, id=product_id).first()
        if not product:
            return "Product does not exist!."

        lines = ["Your Inventory:\n"]
        lines.append(
                f"{product.name}: {product.quantity} units @ {product.selling_price}"
            )

        return lines
    
    # Updates products belonging to a single user from the database
    def update_product(self, product_id: str, data: dict):
        product = self.db.query(Products).filter_by(user_id=self.user_id, id=product_id).first()
        
        if product is None:
            raise
        
        allowed_fields = {
            'quantity',
            'cost_price',
            'selling_price',
            'name',
            'description'
        }
        
        for field in data:
            if field not in allowed_fields:
                continue
            setattr(product, field, data[field])
            
        try:
            self.db.commit()
            self.db.refresh(product)
            return product
        except Exception as e:
            self.db.rollback()
            raise e
        
    # Deletes a specific product for a user
    def delete_product(self, product_id):
        product = self.db.query(Products).filter_by(user_id=self.user_id, id=product_id).first()
        
        try:
            self.db.delete(product)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e