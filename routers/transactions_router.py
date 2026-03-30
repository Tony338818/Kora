# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from dependency.db import get_db
# from services.transaction_service import TransactionService
# from schema.transactions_schema import TransactionCreate
# from dependency.current_user import get_current_user_token

# router = APIRouter(
#     prefix="/transactions", tags=["Transactions"]
#     )


# @router.post("/create")
# def create_transaction(
#     transaction: TransactionCreate,
#     db: Session = Depends(get_db),
#     # user=Depends(get_current_user_token)
# ):
#     return TransactionService.createTransaction(
#         db=db,
#         transaction_data=transaction,
#         # current_user_id=user["userId"]
#         current_user_id=1
#     )
    
# @router.get("/read")
# def get_transactions(
#     db: Session = Depends(get_db),
#     # user=Depends(get_current_user_token)
# ):
#     return TransactionService.readTransactions(
#         db=db,
#         # current_user_id=user["userId"]
#         current_user_id=1
#     )
    

# @router.get("/read/{transaction_id}")
# def get_transaction(
#     transaction_id: int,
#     db: Session = Depends(get_db),
#     # user=Depends(get_current_user_token)
# ):
#     return TransactionService.readTransactionByID(
#         db=db,
#         # current_user_id=user["userId"],
#         current_user_id=1,
#         transaction_id=transaction_id
#     )
    
    
# @router.delete("/delete/{transaction_id}")
# def delete_transaction(
#     # transaction_id: int,
#     db: Session = Depends(get_db),
#     # user=Depends(get_current_user_token)
# ):
#     return TransactionService.deleteTransaction(
#         db=db,
#         # current_user_id=user["userId"],
#         current_user_id=1,
#         # transaction_id=transaction_id
#         transaction_id=1
#     )
    