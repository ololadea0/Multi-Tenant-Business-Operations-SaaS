from decimal import Decimal

from app.api.dependencies import get_current_user
from app.main import app
from app.models.customer import Customer
from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.core.security import hash_password


def create_user(db, email, full_name):
    user = User(
        email=email,
        full_name=full_name,
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_organization(db, name, slug):
    organization = Organization(
        name=name,
        slug=slug,
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization


def add_membership(db, user, organization, role=MembershipRole.OWNER):
    membership = Membership(
        user_id=user.id,
        organization_id=organization.id,
        role=role,
    )

    db.add(membership)
    db.commit()
    db.refresh(membership)

    return membership


def test_user_cannot_access_another_organization(
    client,
    db,
):
    user_a = create_user(
        db,
        "tenant-a@example.com",
        "Tenant A User",
    )

    organization_a = create_organization(
        db,
        "Organization A",
        "organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Organization B",
        "organization-b",
    )

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{organization_b.id}"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have access to this organization"
    )

    app.dependency_overrides.clear()


def test_user_cannot_access_another_organization_products(
    client,
    db,
):
    user_a = create_user(
        db,
        "product-tenant-a@example.com",
        "Product Tenant A",
    )

    organization_a = create_organization(
        db,
        "Product Organization A",
        "product-organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Product Organization B",
        "product-organization-b",
    )

    product_b = Product(
        organization_id=organization_b.id,
        name="Organization B Product",
        sku="ORG-B-001",
        unit_price=Decimal("1000.00"),
        stock_quantity=10,
        low_stock_threshold=2,
    )

    db.add(product_b)
    db.commit()
    db.refresh(product_b)

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{organization_b.id}/products"
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_user_cannot_access_another_organization_customers(
    client,
    db,
):
    user_a = create_user(
        db,
        "customer-tenant-a@example.com",
        "Customer Tenant A",
    )

    organization_a = create_organization(
        db,
        "Customer Organization A",
        "customer-organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Customer Organization B",
        "customer-organization-b",
    )

    customer_b = Customer(
        organization_id=organization_b.id,
        name="Organization B Customer",
        email="customer-b@example.com",
        phone="08000000000",
    )

    db.add(customer_b)
    db.commit()

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{organization_b.id}/customers"
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()


def test_user_cannot_access_another_organization_members(
    client,
    db,
):
    user_a = create_user(
        db,
        "member-tenant-a@example.com",
        "Member Tenant A",
    )

    organization_a = create_organization(
        db,
        "Member Organization A",
        "member-organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Member Organization B",
        "member-organization-b",
    )

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{organization_b.id}/members"
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_user_cannot_update_another_organization_product(
    client,
    db,
):
    user_a = create_user(
        db,
        "product-update-a@example.com",
        "Product Update A",
    )

    organization_a = create_organization(
        db,
        "Update Organization A",
        "update-organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Update Organization B",
        "update-organization-b",
    )

    product_b = Product(
        organization_id=organization_b.id,
        name="Organization B Product",
        sku="ORG-B-UPDATE-001",
        unit_price=Decimal("1000.00"),
        stock_quantity=10,
        low_stock_threshold=2,
    )

    db.add(product_b)
    db.commit()
    db.refresh(product_b)

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.patch(
        f"/api/organizations/{organization_b.id}/products/{product_b.id}",
        json={
            "name": "Hacked Product",
        },
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_user_cannot_delete_another_organization_product(
    client,
    db,
):
    user_a = create_user(
        db,
        "product-delete-a@example.com",
        "Product Delete A",
    )

    organization_a = create_organization(
        db,
        "Delete Organization A",
        "delete-organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Delete Organization B",
        "delete-organization-b",
    )

    product_b = Product(
        organization_id=organization_b.id,
        name="Organization B Product",
        sku="ORG-B-DELETE-001",
        unit_price=Decimal("1000.00"),
        stock_quantity=10,
        low_stock_threshold=2,
    )

    db.add(product_b)
    db.commit()
    db.refresh(product_b)

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.delete(
        f"/api/organizations/{organization_b.id}/products/{product_b.id}"
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_user_cannot_update_another_organization_customer(
    client,
    db,
):
    user_a = create_user(
        db,
        "customer-update-a@example.com",
        "Customer Update A",
    )

    organization_a = create_organization(
        db,
        "Customer Update A",
        "customer-update-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Customer Update B",
        "customer-update-b",
    )

    customer_b = Customer(
        organization_id=organization_b.id,
        name="Organization B Customer",
        email="customer-b-update@example.com",
        phone="08000000000",
    )

    db.add(customer_b)
    db.commit()
    db.refresh(customer_b)

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.patch(
        f"/api/organizations/{organization_b.id}/customers/{customer_b.id}",
        json={
            "name": "Hacked Customer",
        },
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_user_cannot_delete_another_organization_customer(
    client,
    db,
):
    user_a = create_user(
        db,
        "customer-delete-a@example.com",
        "Customer Delete A",
    )

    organization_a = create_organization(
        db,
        "Customer Delete A",
        "customer-delete-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Customer Delete B",
        "customer-delete-b",
    )

    customer_b = Customer(
        organization_id=organization_b.id,
        name="Organization B Customer",
        email="customer-b-delete@example.com",
        phone="08000000000",
    )

    db.add(customer_b)
    db.commit()
    db.refresh(customer_b)

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.delete(
        f"/api/organizations/{organization_b.id}/customers/{customer_b.id}"
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_user_cannot_access_another_organization_orders(
    client,
    db,
):
    user_a = create_user(
        db,
        "order-tenant-a@example.com",
        "Order Tenant A",
    )

    organization_a = create_organization(
        db,
        "Order Organization A",
        "order-organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Order Organization B",
        "order-organization-b",
    )

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{organization_b.id}/orders"
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_user_cannot_access_another_organization_inventory(
    client,
    db,
):
    user_a = create_user(
        db,
        "inventory-tenant-a@example.com",
        "Inventory Tenant A",
    )

    organization_a = create_organization(
        db,
        "Inventory Organization A",
        "inventory-organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Inventory Organization B",
        "inventory-organization-b",
    )

    product_b = Product(
        organization_id=organization_b.id,
        name="Organization B Product",
        sku="INV-B-001",
        unit_price=Decimal("5000.00"),
        stock_quantity=20,
        low_stock_threshold=5,
    )

    db.add(product_b)
    db.commit()
    db.refresh(product_b)

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{organization_b.id}/inventory/{product_b.id}"
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_user_cannot_access_another_organization_inventory(
    client,
    db,
):
    user_a = create_user(
        db,
        "inventory-tenant-a@example.com",
        "Inventory Tenant A",
    )

    organization_a = create_organization(
        db,
        "Inventory Organization A",
        "inventory-organization-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Inventory Organization B",
        "inventory-organization-b",
    )

    product_b = Product(
        organization_id=organization_b.id,
        name="Organization B Product",
        sku="INV-B-001",
        unit_price=Decimal("5000.00"),
        stock_quantity=20,
        low_stock_threshold=5,
    )

    db.add(product_b)
    db.commit()
    db.refresh(product_b)

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{organization_b.id}/products/{product_b.id}/inventory/"
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

def test_user_cannot_modify_another_organization_inventory(
    client,
    db,
):
    user_a = create_user(
        db,
        "inventory-modify-a@example.com",
        "Inventory Modify A",
    )

    organization_a = create_organization(
        db,
        "Inventory Modify Organization A",
        "inventory-modify-a",
    )

    add_membership(db, user_a, organization_a)

    organization_b = create_organization(
        db,
        "Inventory Modify Organization B",
        "inventory-modify-b",
    )

    product_b = Product(
        organization_id=organization_b.id,
        name="Organization B Product",
        sku="INV-B-002",
        unit_price=Decimal("5000.00"),
        stock_quantity=20,
        low_stock_threshold=5,
    )

    db.add(product_b)
    db.commit()
    db.refresh(product_b)

    def override_current_user():
        return user_a

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.post(
        f"/api/organizations/{organization_b.id}/products/{product_b.id}/inventory/",
        json={
            "movement_type": "out",
            "quantity": 5,
            "note": "Unauthorized stock movement",
        },
    )

    assert response.status_code == 403

    db.refresh(product_b)
    assert product_b.stock_quantity == 20

    app.dependency_overrides.clear()
    