from app.models.organization import Organization
from app.models.product import Product


def test_create_product(
    authenticated_client,
    organization,
):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/products",
        json={
            "name": "Laptop",
            "sku": "LAP-001",
            "description": "Test laptop",
            "unit_price": "250000.00",
            "stock_quantity": 10,
            "low_stock_threshold": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Laptop"
    assert data["sku"] == "LAP-001"
    assert data["stock_quantity"] == 10
    assert data["low_stock_threshold"] == 2

def test_user_cannot_access_another_organization_product(
    authenticated_client,
    organization,
    db,
):
    other_organization = Organization(
        name="Other Organization",
        slug="other-organization",
    )

    db.add(other_organization)
    db.commit()
    db.refresh(other_organization)

    product = Product(
        organization_id=other_organization.id,
        name="Private Product",
        sku="PRIVATE-001",
        unit_price="100.00",
        stock_quantity=5,
        low_stock_threshold=1,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    response = authenticated_client.get(
        f"/api/organizations/{organization.id}/products/{product.id}"
    )

    assert response.status_code == 404

def test_negative_product_price_is_rejected(
    authenticated_client,
    organization,
):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/products",
        json={
            "name": "Invalid Product",
            "sku": "INVALID-001",
            "unit_price": "-100.00",
            "stock_quantity": 10,
            "low_stock_threshold": 2,
        },
    )

    assert response.status_code == 422