import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.organization import Organization
from app.models.membership import Membership, MembershipRole
from app.api.dependencies import get_current_user
from app.core.security import hash_password
from decimal import Decimal

from app.models.customer import Customer

from app.models.product import Product



TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not configured")


engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def user(db):
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def organization(db, user):
    organization = Organization(
        name="Test Organization",
        slug="test-organization",
    )

    db.add(organization)
    db.commit()
    db.refresh(organization)

    membership = Membership(
        user_id=user.id,
        organization_id=organization.id,
        role=MembershipRole.OWNER,
    )

    db.add(membership)
    db.commit()

    return organization


@pytest.fixture
def authenticated_client(client, user):
    def override_current_user():
        return user

    app.dependency_overrides[get_current_user] = override_current_user

    return client

@pytest.fixture
def staff_authenticated_client(client, staff_user):
    def override_current_user():
        return staff_user

    app.dependency_overrides[get_current_user] = override_current_user

    return client

@pytest.fixture
def staff_user(db, organization):
    user = User(
        email="staff@example.com",
        full_name="Staff User",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    membership = Membership(
        user_id=user.id,
        organization_id=organization.id,
        role=MembershipRole.STAFF,
    )

    db.add(membership)
    db.commit()

    return user

def test_staff_cannot_create_product(
    client,
    organization,
    staff_user,
):
    def override_current_user():
        return staff_user

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.post(
        f"/api/organizations/{organization.id}/products",
        json={
            "name": "Laptop",
            "sku": "STAFF-001",
            "unit_price": "100000.00",
            "stock_quantity": 5,
            "low_stock_threshold": 1,
        },
    )

    assert response.status_code == 403

    app.dependency_overrides.clear()

@pytest.fixture
def customer(db, organization):
    customer = Customer(
        organization_id=organization.id,
        name="Test Customer",
        email="customer@example.com",
        phone="08012345678",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer

@pytest.fixture
def product(db, organization):
    product = Product(
        organization_id=organization.id,
        name="Test Laptop",
        sku="LAP-TEST-001",
        unit_price=Decimal("250000.00"),
        stock_quantity=10,
        low_stock_threshold=2,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product