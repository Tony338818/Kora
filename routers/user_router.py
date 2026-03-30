# from fastapi.routing import APIRouter
# from fastapi import Depends, Request
# from sqlalchemy.orm import Session
# from schema.user_schema import AuthResponse, Register, Login, Update
# from dependency.db import get_db
# from services.user_service import UserService as us

# router = APIRouter(
#     prefix='/user'
# )

# @router.post('/create', response_model=AuthResponse)
# def create(
#     request: Request, 
#     data: Register,
#     db: Session = Depends(get_db)):
#     try:
#         result = us.create_user(db=db, data=data)
#         return result
#     except Exception as e:
#         return {
#             "success": False,
#             "message": f"Something went wrong. Please try again later. Check {e}"
#         }
    
# @router.post("/read", response_model=AuthResponse)
# def read(
#     request: Request,
#     data: Login,
#     db: Session = Depends(get_db)
# ):
#     try:
#         result = us.read_user_by_phone_number_and_password(db=db, data=data)
#         return result
#     except Exception as e:
#         return {
#             "success": False,
#             "message": f"Something went wrong. Please try again later. Check {e}"
#         }
    
    
# @router.patch('/update/{id}')
# def update(
#     request: Request,
#     id: int,
#     data: Update,
#     db: Session = Depends(get_db)
# ):
#     try:
#         result = us.update_user(db=db, id=id, data=data)
#         return result
#     except Exception as e:
#         return {
#             "success": False,
#             "message": f"Something went wrong. Please try again later. Check {e}"
#         }
    
    
# @router.delete('/delete/{id}')
# def delete(
#     request: Request,
#     id: int,
#     db: Session = Depends(get_db)
# ):
#     try:
#         result = us.delete_user(db=db, id=id)
#         return result
#     except Exception as e:
#         return {
#             "success": False,
#             "message": f"Something went wrong. Please try again later. Check {e}"
#         }