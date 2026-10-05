import pytest

from schema.db_schema import Products
from services.inventory_service import InventoryService



def test_read_product_success(db_session, test_user):
    
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
    result = service.read_product(name='ProductA')
    
    assert result is not None
    assert result['success'] is True
    assert result['data']['name'] == 'producta'
    assert result['data']['quantity'] == 10
    assert result['data']['cost_price'] == 200
    assert result["data"]["selling_price"] == 250
    
    
def test_read_product_missing_name_fails(db_session, test_user):
    
    service = InventoryService(
        db=db_session,
        user_id= test_user.id
    )
    
    data = {
                "name": "ProductA",
                "quantity": 10,
                "cost_price": 200,
                "selling_price": 250,
                "description": "Blah blah blah"
            }
        
    service.create_product(data)
    result = service.read_product(name='')
    
    assert result is not None
    assert result['success'] is False
    
    
def test_read_not_existing_product_name_fails(db_session, test_user):
    
    service = InventoryService(
        db=db_session,
        user_id=test_user.id
    )
    
    result = service.read_product(name='ProductA')
    
    assert result is not None
    assert result['success'] is False
    
def test_read_product_case_insensitive(db_session, test_user):

    service = InventoryService(
        db_session,
        test_user.id
    )

    service.create_product({
        "name": "ProductA",
        "quantity": 10
    })

    result = service.read_product("PRODUCTA")

    assert result["success"] is True
    assert result["data"]["name"] == "producta"
    
    
def test_read_product_ignores_whitespace(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    service.create_product({
        "name": "ProductA",
        "quantity": 10
    })

    result = service.read_product(
        "   ProductA   "
    )

    assert result["success"] is True
    assert result["data"]["name"] == "producta"


def test_user_cannot_read_another_users_product(
    db_session,
    test_user,
    test_userb
):

    service_a = InventoryService(
        db_session,
        test_user.id
    )

    service_b = InventoryService(
        db_session,
        test_userb.id
    )

    service_a.create_product({
        "name": "ProductA",
        "quantity": 10
    })

    result = service_b.read_product(
        "ProductA"
    )

    assert result["success"] is False