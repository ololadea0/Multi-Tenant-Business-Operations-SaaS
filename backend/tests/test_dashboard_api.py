from decimal import Decimal

from app.models.customer import Customer
from app.models.membership import Membership, MembershipRole
from app.models.order import Order, OrderStatus
from app.models.organization import Organization
from app.models.product import Product


def test_dashboard_returns_summary_data(
    authenticated_client,
    organization,
    customer,
    product,
    db,
):
    second_product = Product(
        organization_id=organization.id,
        name="Low Stock Item",
        sku="LOW-001",
        unit_price=Decimal("30.00"),
        stock_quantity=2,
        low_stock_threshold=5,
    )
    db.add(second_product)

    extra_customer = Customer(
        organization_id=organization.id,
        name="Second Customer",
        email="second@example.com",
        phone="08000000002",
    )
    db.add(extra_customer)
    db.flush()

    completed_order = Order(
        organization_id=organization.id,
        customer_id=customer.id,
        created_by_user_id=None,
        status=OrderStatus.COMPLETED,
        total_amount=Decimal("150.00"),
    )
    pending_order = Order(
        organization_id=organization.id,
        customer_id=extra_customer.id,
        created_by_user_id=None,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("75.00"),
    )
    db.add_all([completed_order, pending_order])
    db.commit()

    response = authenticated_client.get(
        f"/api/organizations/{organization.id}/dashboard/"
    )

    assert response.status_code == 200

    payload = response.json()
    overview = payload["overview"]

    assert overview["total_customers"] == 2
    assert overview["total_products"] == 2
    assert overview["total_orders"] == 2
    assert overview["completed_orders"] == 1
    assert Decimal(str(overview["total_revenue"])) == Decimal("150.00")
    assert overview["low_stock_products"] == 1

    assert payload["today"]["orders"] >= 0
    assert payload["this_week"]["orders"] >= 0
    assert payload["this_month"]["orders"] >= 0
    assert len(payload["low_stock_items"]) == 1
    assert payload["low_stock_items"][0]["sku"] == "LOW-001"
    assert len(payload["recent_orders"]) == 2


def test_dashboard_isolates_organization_data(
    authenticated_client,
    organization,
    user,
    customer,
    product,
    db,
):
    other_org = Organization(
        name="Other Org",
        slug="other-org",
    )
    db.add(other_org)
    db.flush()

    membership = Membership(
        user_id=user.id,
        organization_id=other_org.id,
        role=MembershipRole.OWNER,
    )
    db.add(membership)

    other_customer = Customer(
        organization_id=other_org.id,
        name="Other Customer",
        email="other-customer@example.com",
        phone="08000000003",
    )
    db.add(other_customer)
    db.flush()

    other_product = Product(
        organization_id=other_org.id,
        name="Other Product",
        sku="OTHER-001",
        unit_price=Decimal("900.00"),
        stock_quantity=10,
        low_stock_threshold=12,
    )
    completed_other_order = Order(
        organization_id=other_org.id,
        customer_id=other_customer.id,
        created_by_user_id=user.id,
        status=OrderStatus.COMPLETED,
        total_amount=Decimal("999.00"),
    )
    db.add_all([other_product, completed_other_order])
    db.commit()

    response = authenticated_client.get(
        f"/api/organizations/{organization.id}/dashboard/"
    )

    payload = response.json()
    overview = payload["overview"]

    assert overview["total_customers"] == 1
    assert overview["total_products"] == 1
    assert overview["total_orders"] == 0
    assert overview["completed_orders"] == 0
    assert Decimal(str(overview["total_revenue"])) == Decimal("0.00")
    assert overview["low_stock_products"] == 0


def test_dashboard_requires_membership(
    client,
    organization,
):
    response = client.get(
        f"/api/organizations/{organization.id}/dashboard/"
    )

    assert response.status_code == 401


def test_dashboard_allows_staff_member_access(
    client,
    organization,
    staff_user,
    db,
):
    from app.api.dependencies import get_current_user
    from app.main import app as fastapi_app

    fastapi_app.dependency_overrides[get_current_user] = lambda: staff_user

    try:
        response = client.get(
            f"/api/organizations/{organization.id}/dashboard/"
        )
        assert response.status_code == 200
        assert response.json()["overview"]["total_customers"] >= 0
    finally:
        fastapi_app.dependency_overrides.clear()
