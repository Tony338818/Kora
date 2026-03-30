# from fastapi.routing import APIRouter
# from fastapi import Request, Depends
# from sqlalchemy.orm import Session
# from services.inventory_service import InventoryService as ivs
# from dependency.db import get_db
# from schema.product_schema import ProductCreate, ProductDisplay, ProductResponse, ProductUpdate
# from dependency.current_user import get_current_user_token

# router = APIRouter(
#     prefix='/inventory'
# )

# @router.post('/create', response_model=ProductResponse)
# def create(
#     request: Request,
#     data: ProductCreate,
#     # user_id: int = Depends(get_current_user_token),
#     db: Session = Depends(get_db)
# ):
#     try:
#         result = ivs.createProduct(db=db, product_data=data, current_user_id=1)
#         return result
#     except Exception as e:
#         return {
#             'success': False,
#             'message': f'{e}'
#         }
        
# @router.get('/read', response_model=ProductDisplay)
# def create(
#     request: Request,
#     # user_id: int = Depends(get_current_user_token),
#     db: Session = Depends(get_db)
# ):
#     try:
#         result = ivs.readProducts(db=db, current_user_id=1)
#         return result
#     except Exception as e:
#         return {
#             'success': False,
#             'message': f'{e}'
#         }
        
# @router.patch('/update', response_model=ProductResponse)
# def create(
#     request: Request,
#     # user_id: int = Depends(get_current_user_token),
#     data: ProductUpdate,
#     db: Session = Depends(get_db)
# ):
#     try:
#         result = ivs.updateProduct(db=db, current_user_id=1, product_id=24, data=data)
#         return result
#     except Exception as e:
#         return {
#             'success': False,
#             'message': f'{e}'
#         }
        
# @router.delete('/delete', response_model=ProductResponse)
# def create(
#     request: Request,
#     # user_id: int = Depends(get_current_user_token),
#     db: Session = Depends(get_db)
# ):
#     try:
#         result = ivs.deleteProduct(db=db, current_user_id=1, product_id=23)
#         return result
#     except Exception as e:
#         return {
#             'success': False,
#             'message': f'{e}'
#         }