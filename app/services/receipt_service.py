from sqlalchemy.orm import Session
from schema.db_schema import Transactions

class ReceiptService:

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _get_transaction(self, transaction_id: int):
        """
        Fetch transaction belonging to current user.
        """

        return (
            self.db.query(Transactions)
            .filter_by(
                id=transaction_id,
                user_id=self.user_id
            )
            .first()
        )


    # --------------------------------------------------
    # Public Method
    # --------------------------------------------------

    def generate_receipt(self, transaction_id: int):

        transaction = self._get_transaction(
            transaction_id
        )


        if not transaction:
            return {
                "success": False,
                "message": "Transaction not found."
            }


        divider = "─" * 35


        lines = [
            divider,
            "              RECEIPT",
            divider,
            f"Transaction ID : #{transaction.id}",
            f"Type           : {transaction.transaction_type.title()}",
            f"Payment Method : {transaction.payment_method or 'N/A'}",
            f"Payment Status : {transaction.payment_status or 'N/A'}",
            f"Date           : {transaction.created_at}",
            divider,
            "Items:",
        ]


        for item in transaction.items:

            lines.append(
                f"{item.product_name.title()}"
            )

            lines.append(
                f"  {item.quantity} x "
                f"{item.unit_price} = "
                f"{item.subtotal}"
            )


        lines.extend(
            [
                divider,
                f"TOTAL : {transaction.amount}",
                divider,
                "Thank you for your business!"
            ]
        )


        return {
            "success": True,
            "data": "\n".join(lines)
        }