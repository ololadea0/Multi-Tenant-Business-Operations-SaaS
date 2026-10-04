from decimal import Decimal

from app.models.customer import Customer
from app.models.inventory import InventoryMovement, InventoryMovementType
from app.models.product import Product
from app.models.order import Order, OrderStatus

from app.main import app
from app.api.dependencies import get_current_user


def test_create_order(
    authenticated_client,
    organization,
    customer,
    product,
    db,
):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/",
        json={
            "customer_id": customer.id,
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()["order"]

    assert data["customer_id"] == customer.id
    assert data["status"] == OrderStatus.CONFIRMED
    assert Decimal(str(data["total_amount"])) == Decimal("500000.00")

    db.refresh(product)

    assert product.stock_quantity == 8

    movement = (
        db.query(InventoryMovement)
        .filter(
            InventoryMovement.product_id == product.id
        )
        .first()
    )

    assert movement is not None
    assert movement.movement_type == InventoryMovementType.OUT
    assert movement.quantity == 2
    assert movement.previous_stock == 10
    assert movement.new_stock == 8

def test_create_order_with_insufficient_stock(
    authenticated_client,
    organization,
    customer,
    product,
    db,
):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/",
        json={
            "customer_id": customer.id,
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 11,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]

    db.refresh(product)

    assert product.stock_quantity == 10

    assert db.query(Order).count() == 0
    assert db.query(InventoryMovement).count() == 0

def test_create_order_with_invalid_customer(
    authenticated_client,
    organization,
    product,
):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/",
        json={
            "customer_id": 999999,
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"

def test_duplicate_product_in_order_is_rejected(
    authenticated_client,
    organization,
    customer,
    product,
):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/",
        json={
            "customer_id": customer.id,
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                },
                {
                    "product_id": product.id,
                    "quantity": 2,
                },
            ],
        },
    )

    assert response.status_code == 422

def test_cancel_order_restores_stock(
    authenticated_client,
    organization,
    customer,
    product,
    db,
):
    create_response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/",
        json={
            "customer_id": customer.id,
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 3,
                }
            ],
        },
    )

    assert create_response.status_code == 200

    order_id = create_response.json()["order"]["id"]

    db.refresh(product)
    assert product.stock_quantity == 7

    cancel_response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/{order_id}/cancel"
    )

    assert cancel_response.status_code == 200

    db.refresh(product)

    assert product.stock_quantity == 10

    movements = (
        db.query(InventoryMovement)
        .filter(
            InventoryMovement.product_id == product.id
        )
        .order_by(InventoryMovement.id)
        .all()
    )

    assert len(movements) == 2

    assert movements[0].movement_type == InventoryMovementType.OUT
    assert movements[0].quantity == 3

    assert movements[1].movement_type == InventoryMovementType.IN
    assert movements[1].quantity == 3

def test_cannot_cancel_order_twice(
    authenticated_client,
    organization,
    customer,
    product,
):
    create_response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/",
        json={
            "customer_id": customer.id,
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 2,
                }
            ],
        },
    )

    order_id = create_response.json()["order"]["id"]

    first_cancel = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/{order_id}/cancel"
    )

    assert first_cancel.status_code == 200

    second_cancel = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/{order_id}/cancel"
    )

    assert second_cancel.status_code == 400
    assert second_cancel.json()["detail"] == "Order is already cancelled"

def test_completed_order_cannot_be_cancelled(
    authenticated_client,
    organization,
    customer,
    product,
):
    create_response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/",
        json={
            "customer_id": customer.id,
            "items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                }
            ],
        },
    )

    order_id = create_response.json()["order"]["id"]

    complete_response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/{order_id}/complete"
    )

    assert complete_response.status_code == 200

    cancel_response = authenticated_client.post(
        f"/api/organizations/{organization.id}/orders/{order_id}/cancel"
    )

    assert cancel_response.status_code == 400
    assert (
        cancel_response.json()["detail"]
        == "Completed orders cannot be cancelled"
    )