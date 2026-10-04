from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.models.inventory import InventoryMovementType
from app.services.inventory import change_stock


class FakeDB:
    def add(self, obj):
        self.added = obj


def make_product(
    product_id=1,
    organization_id=1,
    stock_quantity=10,
    name="Test Product"
):
    return SimpleNamespace(
        id=product_id,
        organization_id=organization_id,
        stock_quantity=stock_quantity,
        name=name,
    )


def test_stock_in():
    db = FakeDB()
    product = make_product(stock_quantity=10)

    movement = change_stock(
        db=db,
        organization_id=1,
        product=product,
        movement_type=InventoryMovementType.IN,
        quantity=5,
        user_id=1,
    )

    assert product.stock_quantity == 15
    assert movement.previous_stock == 10
    assert movement.new_stock == 15
    assert movement.quantity == 5
    assert movement.movement_type == InventoryMovementType.IN


def test_stock_out():
    db = FakeDB()
    product = make_product(stock_quantity=10)

    movement = change_stock(
        db=db,
        organization_id=1,
        product=product,
        movement_type=InventoryMovementType.OUT,
        quantity=4,
        user_id=1,
    )

    assert product.stock_quantity == 6
    assert movement.previous_stock == 10
    assert movement.new_stock == 6


def test_stock_out_rejects_insufficient_stock():
    db = FakeDB()
    product = make_product(stock_quantity=3)

    with pytest.raises(HTTPException) as exc:
        change_stock(
            db=db,
            organization_id=1,
            product=product,
            movement_type=InventoryMovementType.OUT,
            quantity=5,
            user_id=1,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Insufficient stock"
    assert product.stock_quantity == 3


def test_adjustment_can_increase_stock():
    db = FakeDB()
    product = make_product(stock_quantity=10)

    change_stock(
        db=db,
        organization_id=1,
        product=product,
        movement_type=InventoryMovementType.ADJUSTMENT,
        quantity=7,
        user_id=1,
    )

    assert product.stock_quantity == 17


def test_adjustment_can_decrease_stock():
    db = FakeDB()
    product = make_product(stock_quantity=10)

    change_stock(
        db=db,
        organization_id=1,
        product=product,
        movement_type=InventoryMovementType.ADJUSTMENT,
        quantity=-4,
        user_id=1,
    )

    assert product.stock_quantity == 6


def test_adjustment_cannot_create_negative_stock():
    db = FakeDB()
    product = make_product(stock_quantity=3)

    with pytest.raises(HTTPException) as exc:
        change_stock(
            db=db,
            organization_id=1,
            product=product,
            movement_type=InventoryMovementType.ADJUSTMENT,
            quantity=-5,
            user_id=1,
        )

    assert exc.value.status_code == 400
    assert (
        exc.value.detail
        == "Adjustment cannot reduce stock below zero"
    )
    assert product.stock_quantity == 3


def test_zero_quantity_is_rejected():
    db = FakeDB()
    product = make_product(stock_quantity=10)

    with pytest.raises(HTTPException) as exc:
        change_stock(
            db=db,
            organization_id=1,
            product=product,
            movement_type=InventoryMovementType.IN,
            quantity=0,
            user_id=1,
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Stock quantity cannot be zero"


def test_product_from_another_organization_is_rejected():
    db = FakeDB()
    product = make_product(organization_id=2)

    with pytest.raises(HTTPException) as exc:
        change_stock(
            db=db,
            organization_id=1,
            product=product,
            movement_type=InventoryMovementType.IN,
            quantity=5,
            user_id=1,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "Product not found"