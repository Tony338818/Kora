from sqlalchemy.orm import Session
from schema.db_schema import Transactions, TransactionItem, Products

class SalesService:
    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id


    def _get_product(self, product_name: str):
        """Find product belonging to current user."""

        return (
            self.db.query(Products)
            .filter_by(
                user_id=self.user_id,
                name=product_name.lower()
            )
            .first()
        )


    def _create_transaction(self, data: dict, transaction_type: str):

        items_data = data.get("items", [])

        if not items_data:
            return {
                "success": False,
                "message": "No items provided."
            }


        try:
            total_amount = 0
            transaction_items = []


            for item in items_data:

                product_name = item.get("product_name")
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0)


                product = self._get_product(product_name)


                if not product:
                    raise ValueError(
                        f"{product_name} does not exist."
                    )


                # -----------------------------
                # Update Inventory
                # -----------------------------

                if transaction_type == "sale":

                    if product.quantity < quantity:
                        raise ValueError(
                            f"Not enough {product.name} in stock."
                        )

                    product.quantity -= quantity


                elif transaction_type == "purchase":

                    product.quantity += quantity



                subtotal = quantity * unit_price

                total_amount += subtotal


                transaction_items.append(
                    TransactionItem(
                        product_id=product.id,
                        product_name=product.name,
                        quantity=quantity,
                        unit_price=unit_price,
                        subtotal=subtotal
                    )
                )


            # -----------------------------
            # Create Transaction
            # -----------------------------

            transaction = Transactions(
                user_id=self.user_id,
                transaction_type=transaction_type,
                amount=total_amount,
                payment_method=data.get("payment_method"),
                payment_status=data.get(
                    "payment_status",
                    "paid"
                ),
                customer_name=data.get(
                    "customer_name"
                ),
                customer_phone=data.get(
                    "customer_phone"
                ),
                items=transaction_items
            )


            self.db.add(transaction)

            self.db.commit()

            self.db.refresh(transaction)



            return {
                "success": True,
                "message": (
                    f"{transaction_type.title()} "
                    "recorded successfully."
                ),
                "data": {
                    "transaction_id": transaction.id,
                    "amount": transaction.amount
                }
            }


        except Exception as e:

            self.db.rollback()

            return {
                "success": False,
                "message": str(e)
            }


    def record_sale(self, data: dict):

        return self._create_transaction(
            data,
            transaction_type="sale"
        )


    def record_purchase(self, data: dict):

        return self._create_transaction(
            data,
            transaction_type="purchase"
        )