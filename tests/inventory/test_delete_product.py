import pytest

from schema.db_schema import Products
from services.inventory_service import InventoryService


def test_delete_success(db_session, test_user):
    
    service = InventoryService(
        db=db_session,
        user_id=test_user.id
    )
    
    data = {
        "name": "ProductA",
        "quantity": 10,
        "cost_price": 200,
        "selling_price": 250,
        "description": "Blah blah blah"
    }

    service.create_product(data)

    result = service.delete_product(name="ProductA")
    
    product = (db_session.query(Products).
                   filter_by(
                       user_id=test_user.id,
                       name='producta'
                   ).first())
    
    assert result['success'] is True   
    assert product is None
    
def test_delete_missing_names_fails(db_session, test_user):
    service = InventoryService(
            db=db_session,
            user_id=test_user.id
        )

    result = service.delete_product(name="ProductA")
    
    assert result['success'] is False
    
def test_delete_empty_names_fails(db_session, test_user):
    service = InventoryService(
            db=db_session,
            user_id=test_user.id
        )

    result = service.delete_product(name="")
    
    assert result['success'] is False
    
def test_user_cannot_delete_another_users_product(db_session, test_user, test_userb):
    service = InventoryService(
            db=db_session,
            user_id=test_user.id
        )
    
    serviceb = InventoryService(
            db=db_session,
            user_id=test_userb.id
        )
    
    data = {
            "name": "ProductA",
            "quantity": 10,
            "cost_price": 200,
            "selling_price": 250,
            "description": "Blah blah blah"
        }
    
    service.create_product(data)
    
    result = serviceb.delete_product(name='ProductA')
    
    product = (db_session.query(Products).
                filter_by(
                    user_id=test_user.id,
                    name='producta'
                ).first()
                )
    
    assert result['success'] is False
    assert product is not None
    
def test_delete_product_name_is_normalized(
    db_session,
    test_user
):
    service = InventoryService(
        db=db_session,
        user_id=test_user.id
    )

    service.create_product({
        "name": "ProductA",
        "quantity": 10
    })

    result = service.delete_product(
        name="   PRODUCTA   "
    )

    assert result["success"] is True

    product = service.get_product_by_name(
        "ProductA"
    )

    assert product is None