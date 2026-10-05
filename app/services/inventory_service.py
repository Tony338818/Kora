from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from schema.db_schema import Products
from schema.product_schema import ProductCreate, ProductUpdate


class InventoryService:

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    # -----------------------------------------------------
    # Helpers
    # -----------------------------------------------------

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower()

    def get_product_by_name(self, name: str) -> Products | None:
        """
        Fetch a product belonging to the current user by name.
        """

        name = self._normalize_name(name)

        return (
            self.db.query(Products)
            .filter(
                Products.user_id == self.user_id,
                Products.name == name
            )
            .first()
        )

    def _serialize_product(self, product: Products) -> dict:
        return {
            "id": product.id,
            "name": product.name,
            "quantity": product.quantity,
            "cost_price": product.cost_price,
            "selling_price": product.selling_price,
            "description": product.description,
            "img_url": product.img_url,
        }

    # -----------------------------------------------------
    # Create
    # -----------------------------------------------------

    def create_product(self, data: dict):

        try:
            product_data = ProductCreate(**data)

            name = self._normalize_name(product_data.name)
            
            if len(name) < 2:
                 return {
                    "success": False,
                    "message": (
                        f"Please Enter a valid Name!s"
                    )
                }

            existing_product = self.get_product_by_name(name)

            if existing_product:
                return {
                    "success": False,
                    "message": (
                        f"'{name.title()}' already exists "
                        "in your inventory."
                    )
                }

            new_product = Products(
                user_id=self.user_id,
                **product_data.model_dump()
            )

            new_product.name = name

            self.db.add(new_product)
            self.db.commit()
            self.db.refresh(new_product)

            return {
                "success": True,
                "message": (
                    f"'{new_product.name.title()}' added "
                    f"with {new_product.quantity} units."
                ),
                "data": self._serialize_product(new_product)
            }

        except IntegrityError:
            self.db.rollback()

            return {
                "success": False,
                "message": "That product already exists."
            }

        except Exception as error:
            self.db.rollback()

            return {
                "success": False,
                "message": f"Failed to add product: {error}"
            }

    # -----------------------------------------------------
    # Read
    # -----------------------------------------------------

    def read_all_products(self):

        products = (
            self.db.query(Products)
            .filter(
                Products.user_id == self.user_id
            )
            .order_by(Products.name)
            .all()
        )

        if not products:
            return {
                "success": True,
                "message": "Your inventory is empty.",
                "data": []
            }

        lines = ["Your inventory:"]

        for product in products:

            price = (
                f" @ £{product.selling_price:.2f}"
                if product.selling_price is not None
                else ""
            )

            lines.append(
                f"• {product.name.title()}: "
                f"{product.quantity} units{price}"
            )

        return {
            "success": True,
            "message": "\n".join(lines),
            "data": [
                self._serialize_product(product)
                for product in products
            ]
        }

    def read_product(self, name: str):

        product = self.get_product_by_name(name)

        if not product:
            return {
                "success": False,
                "message": (
                    f"I couldn't find '{name}' "
                    "in your inventory."
                )
            }

        price = (
            f"£{product.selling_price:.2f}"
            if product.selling_price is not None
            else "not set"
        )

        return {
            "success": True,
            "message": (
                f"{product.name.title()}: "
                f"{product.quantity} units, "
                f"selling price {price}."
            ),
            "data": self._serialize_product(product)
        }

    # -----------------------------------------------------
    # Update product details
    # -----------------------------------------------------

    def update_product(self, name: str, data: dict):

        product = self.get_product_by_name(name)

        if not product:
            return {
                "success": False,
                "message": (
                    f"I couldn't find '{name}' "
                    "in your inventory."
                )
            }

        try:
            update_data = ProductUpdate(**data)

            changes = update_data.model_dump(
                exclude_unset=True,
                exclude_none=True
            )

            if "name" in changes:
                changes["name"] = self._normalize_name(
                    changes["name"]
                )

            for field, value in changes.items():
                setattr(product, field, value)

            self.db.commit()
            self.db.refresh(product)

            return {
                "success": True,
                "message": (
                    f"'{product.name.title()}' "
                    "updated successfully."
                ),
                "data": self._serialize_product(product)
            }

        except IntegrityError:
            self.db.rollback()

            return {
                "success": False,
                "message": (
                    "A product with that name "
                    "already exists."
                )
            }

        except Exception as error:
            self.db.rollback()

            return {
                "success": False,
                "message": f"Failed to update product: {error}"
            }

    # -----------------------------------------------------
    # Delete
    # -----------------------------------------------------

    def delete_product(self, name: str):

        product = self.get_product_by_name(name)

        if not product:
            return {
                "success": False,
                "message": (
                    f"I couldn't find '{name}' "
                    "in your inventory."
                )
            }

        try:
            product_name = product.name

            self.db.delete(product)
            self.db.commit()

            return {
                "success": True,
                "message": (
                    f"'{product_name.title()}' "
                    "removed from your inventory."
                )
            }

        except Exception as error:
            self.db.rollback()

            return {
                "success": False,
                "message": f"Failed to delete product: {error}"
            }