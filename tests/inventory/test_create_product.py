import pytest

from schema.db_schema import Products
from services.inventory_service import InventoryService


# ---------------------------------------------------------
# Successful Creation
# ---------------------------------------------------------

def test_create_product_success(db_session, test_user):

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

    result = service.create_product(data)

    assert result["success"] is True

    product = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .first()
    )

    assert product is not None
    assert product.user_id == test_user.id
    assert product.name == "producta"
    assert product.quantity == 10
    assert product.cost_price == 200
    assert product.selling_price == 250
    assert product.description == "Blah blah blah"


def test_create_product_success_with_minimal_values(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    data = {
        "name": "ProductB"
    }

    result = service.create_product(data)

    assert result["success"] is True

    product = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="productb"
        )
        .first()
    )

    assert product is not None
    assert product.quantity == 0
    assert product.cost_price is None
    assert product.selling_price is None
    assert product.description is None


# ---------------------------------------------------------
# Duplicate Products
# ---------------------------------------------------------

def test_duplicate_entries_fail(db_session, test_user):

    service = InventoryService(
        db_session,
        test_user.id
    )

    data = {
        "name": "ProductA",
        "quantity": 10,
        "cost_price": 200,
        "selling_price": 250
    }

    first_result = service.create_product(data)
    second_result = service.create_product(data)

    assert first_result["success"] is True
    assert second_result["success"] is False

    products = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .all()
    )

    assert len(products) == 1


def test_case_insensitive_duplicate_entries_fail(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    first_result = service.create_product({
        "name": "ProductA"
    })

    second_result = service.create_product({
        "name": "PRODUCTA"
    })

    assert first_result["success"] is True
    assert second_result["success"] is False

    products = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .all()
    )

    assert len(products) == 1


def test_cross_user_duplicate_success(
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

    data = {
        "name": "ProductA",
        "quantity": 10
    }

    result_a = service_a.create_product(data)
    result_b = service_b.create_product(data)

    assert result_a["success"] is True
    assert result_b["success"] is True

    product_a = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .first()
    )

    product_b = (
        db_session.query(Products)
        .filter_by(
            user_id=test_userb.id,
            name="producta"
        )
        .first()
    )

    assert product_a is not None
    assert product_b is not None

    assert product_a.user_id != product_b.user_id


# ---------------------------------------------------------
# Invalid Numeric Values
# ---------------------------------------------------------

def test_negative_quantity_fails(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "ProductA",
        "quantity": -1
    })

    assert result["success"] is False

    product = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .first()
    )

    assert product is None


def test_negative_cost_price_fails(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "ProductA",
        "cost_price": -10
    })

    assert result["success"] is False

    product = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .first()
    )

    assert product is None


def test_negative_selling_price_fails(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "ProductA",
        "selling_price": -10
    })

    assert result["success"] is False

    product = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .first()
    )

    assert product is None


# ---------------------------------------------------------
# Boundary Numeric Values
# ---------------------------------------------------------

def test_zero_quantity_is_valid(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "ProductA",
        "quantity": 0
    })

    assert result["success"] is True

    product = service.get_product_by_name(
        "ProductA"
    )

    assert product is not None
    assert product.quantity == 0


def test_zero_prices_are_valid(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "ProductA",
        "cost_price": 0,
        "selling_price": 0
    })

    assert result["success"] is True

    product = service.get_product_by_name(
        "ProductA"
    )

    assert product is not None
    assert product.cost_price == 0
    assert product.selling_price == 0


# ---------------------------------------------------------
# Invalid Product Names
# ---------------------------------------------------------

def test_empty_name_fails(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": ""
    })

    assert result["success"] is False

    products = (
        db_session.query(Products)
        .filter_by(user_id=test_user.id)
        .all()
    )

    assert len(products) == 0


def test_missing_name_fails(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "quantity": 10
    })

    assert result["success"] is False

    products = (
        db_session.query(Products)
        .filter_by(user_id=test_user.id)
        .all()
    )

    assert len(products) == 0


def test_whitespace_only_name_fails(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "     "
    })

    assert result["success"] is False

    products = (
        db_session.query(Products)
        .filter_by(user_id=test_user.id)
        .all()
    )

    assert len(products) == 0


def test_name_over_100_characters_fails(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "A" * 101
    })

    assert result["success"] is False

    products = (
        db_session.query(Products)
        .filter_by(user_id=test_user.id)
        .all()
    )

    assert len(products) == 0


# ---------------------------------------------------------
# Description Validation
# ---------------------------------------------------------

def test_description_over_255_characters_fails(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "ProductA",
        "description": "A" * 256
    })

    assert result["success"] is False

    product = service.get_product_by_name(
        "ProductA"
    )

    assert product is None


# ---------------------------------------------------------
# Name Normalization
# ---------------------------------------------------------

def test_product_name_whitespace_is_normalized(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "   ProductA   "
    })

    assert result["success"] is True

    product = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .first()
    )

    assert product is not None
    assert product.name == "producta"


# ---------------------------------------------------------
# Serialized Response
# ---------------------------------------------------------

def test_create_product_returns_correct_format(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "ProductA",
        "quantity": 10,
        "cost_price": 200,
        "selling_price": 250,
        "description": "Test product"
    })

    assert isinstance(result, dict)

    assert "success" in result
    assert "message" in result
    assert "data" in result

    assert isinstance(result["success"], bool)
    assert isinstance(result["message"], str)
    assert isinstance(result["data"], dict)

    assert result["success"] is True

    data = result["data"]

    assert data["id"] is not None
    assert data["name"] == "producta"
    assert data["quantity"] == 10
    assert data["cost_price"] == 200
    assert data["selling_price"] == 250
    assert data["description"] == "Test product"


def test_response_matches_persisted_product(
    db_session,
    test_user
):

    service = InventoryService(
        db_session,
        test_user.id
    )

    result = service.create_product({
        "name": "ProductA",
        "quantity": 10,
        "selling_price": 250
    })

    product = (
        db_session.query(Products)
        .filter_by(
            user_id=test_user.id,
            name="producta"
        )
        .first()
    )

    assert product is not None

    assert result["data"]["id"] == product.id
    assert result["data"]["name"] == product.name
    assert result["data"]["quantity"] == product.quantity
    assert (
        result["data"]["selling_price"]
        == product.selling_price
    )