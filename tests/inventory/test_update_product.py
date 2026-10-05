import pytest

from schema.db_schema import Products
from services.inventory_service import InventoryService

    

def test_update_product_success(db_session, test_user):
    
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
    
    update_data = {
        'quantity': 20,
    }
    
    result = service.update_product(name='ProductA', data=update_data)
    
    product = (db_session.query(Products).
               filter_by(
                   user_id = test_user.id,
                   name="producta"
               ).first()
               )
    
    assert result is not None
    assert result['success'] is True
    assert product is not None
    assert product.quantity == 20
    
    
def test_update_product_empty_name_fails(db_session, test_user):
    
    service = InventoryService(
        db=db_session,
        user_id = test_user.id
    )
    
    data = {
            "name": "ProductA",
            "quantity": 10,
            "cost_price": 200,
            "selling_price": 250,
            "description": "Blah blah blah"
        }
    
    service.create_product(data)
    
    update_data = {
        'quantity': 20,
    }
    
    result = service.update_product(name='', data=update_data)
    
    product = (db_session.query(Products).
                filter_by(
                    user_id = test_user.id,
                    name="producta"
                ).first()
                )
    
    assert result is not None
    assert result['success'] is False
    assert product is not None
    assert product.quantity == 10
    
    
def test_update_missing_product_fails(db_session, test_user):
    
    service = InventoryService(
        db=db_session,
        user_id = test_user.id
    )
    
    update_data = {
        'quantity': 20,
    }
    
    result = service.update_product(name='ProductA', data=update_data)
    
    product = (db_session.query(Products).
                filter_by(
                    user_id = test_user.id,
                    name="producta"
                ).first()
                )
    
    assert result is not None
    assert result['success'] is False
    assert product is None
    
def test_update_negative_quantity_fails(
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

    result = service.update_product(
        name="ProductA",
        data={"quantity": -20}
    )

    product = service.get_product_by_name(
        "ProductA"
    )

    assert result["success"] is False
    assert product.quantity == 10
    

def test_update_multiple_fields_success(
    db_session,
    test_user
):
    service = InventoryService(
        db_session,
        test_user.id
    )

    service.create_product({
        "name": "ProductA",
        "quantity": 10,
        "cost_price": 200,
        "selling_price": 250
    })

    result = service.update_product(
        "ProductA",
        {
            "quantity": 20,
            "cost_price": 220,
            "selling_price": 300,
            "description": "Updated description"
        }
    )

    product = service.get_product_by_name(
        "ProductA"
    )

    assert result["success"] is True
    assert product.quantity == 20
    assert product.cost_price == 220
    assert product.selling_price == 300
    assert product.description == "Updated description"
    
    
def test_update_product_name_success(
    db_session,
    test_user
):
    service = InventoryService(
        db_session,
        test_user.id
    )

    service.create_product({
        "name": "ProductA"
    })

    result = service.update_product(
        "ProductA",
        {"name": "ProductB"}
    )

    assert result["success"] is True

    old_product = service.get_product_by_name(
        "ProductA"
    )

    new_product = service.get_product_by_name(
        "ProductB"
    )

    assert old_product is None
    assert new_product is not None
    assert new_product.name == "productb"
    
    
def test_rename_to_existing_product_fails(
    db_session,
    test_user
):
    service = InventoryService(
        db_session,
        test_user.id
    )

    service.create_product({"name": "Coke"})
    service.create_product({"name": "Sprite"})

    result = service.update_product(
        "Sprite",
        {"name": "Coke"}
    )

    assert result["success"] is False

    coke = service.get_product_by_name("Coke")
    sprite = service.get_product_by_name("Sprite")

    assert coke is not None
    assert sprite is not None
    
    
def test_user_cannot_update_another_users_product(
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

    result = service_b.update_product(
        "ProductA",
        {"quantity": 999}
    )

    assert result["success"] is False

    product = service_a.get_product_by_name(
        "ProductA"
    )

    assert product.quantity == 10