from sqlalchemy.orm import Session

from schema.db_schema import Transactions


class TransactionService:

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _get_transaction(self, transaction_id: int):
        """
        Get a transaction belonging to the current user.
        """

        return (
            self.db.query(Transactions)
            .filter_by(
                id=transaction_id,
                user_id=self.user_id
            )
            .first()
        )


    def _format_transaction(self, transaction: Transactions):
        """
        Convert transaction object into readable text.
        """

        lines = [
            f"Transaction #{transaction.id}",
            f"Type           : {transaction.transaction_type.title()}",
            f"Amount         : {transaction.amount}",
            f"Payment Method : {transaction.payment_method or 'N/A'}",
            f"Payment Status : {transaction.payment_status or 'N/A'}",
            f"Date           : {transaction.created_at}",
            "",
            "Items:"
        ]


        for item in transaction.items:
            lines.append(
                f"• {item.product_name.title()} "
                f"x{item.quantity} "
                f"@ {item.unit_price} "
                f"= {item.subtotal}"
            )


        return "\n".join(lines)

    # --------------------------------------------------
    # Public Methods
    # --------------------------------------------------

    def get_transaction(self, transaction_id: int):

        transaction = self._get_transaction(
            transaction_id
        )


        if not transaction:
            return {
                "success": False,
                "message": "Transaction not found."
            }


        return {
            "success": True,
            "data": self._format_transaction(transaction)
        }



    def list_transactions(self):

        transactions = (
            self.db.query(Transactions)
            .filter_by(
                user_id=self.user_id
            )
            .order_by(
                Transactions.created_at.desc()
            )
            .all()
        )


        if not transactions:
            return {
                "success": False,
                "message": "You have no transactions yet."
            }



        lines = [
            f"Transactions ({len(transactions)} total)\n"
        ]


        for transaction in transactions:

            lines.append(
                f"#{transaction.id} | "
                f"{transaction.transaction_type.title()} | "
                f"Amount: {transaction.amount} | "
                f"Status: {transaction.payment_status}"
            )


        return {
            "success": True,
            "data": "\n".join(lines)
        }