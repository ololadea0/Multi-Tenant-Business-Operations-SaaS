from app.models.customer import Customer
from app.models.membership import Membership, MembershipRole


def test_create_customer(authenticated_client, organization):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/customers/",
        json={
            "name": "Test Customer",
            "email": "customer@example.com",
            "phone": "08012345678",
            "address": "Ibadan, Nigeria",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test Customer"
    assert data["email"] == "customer@example.com"
    assert data["phone"] == "08012345678"


def test_list_customers(authenticated_client, organization, customer):
    response = authenticated_client.get(
        f"/api/organizations/{organization.id}/customers/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == customer.id
    assert data[0]["name"] == customer.name


def test_get_customer(authenticated_client, organization, customer):
    response = authenticated_client.get(
        f"/api/organizations/{organization.id}/customers/{customer.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer.id
    assert data["name"] == customer.name


def test_get_nonexistent_customer(authenticated_client, organization):
    response = authenticated_client.get(
        f"/api/organizations/{organization.id}/customers/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_update_customer(authenticated_client, organization, customer):
    response = authenticated_client.patch(
        f"/api/organizations/{organization.id}/customers/{customer.id}",
        json={
            "name": "Updated Customer",
            "phone": "08123456789",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Customer"
    assert data["phone"] == "08123456789"


def test_delete_customer(authenticated_client, organization, customer):
    response = authenticated_client.delete(
        f"/api/organizations/{organization.id}/customers/{customer.id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Customer deleted successfully"


def test_staff_cannot_create_customer(
    staff_authenticated_client,
    organization,
):
    response = staff_authenticated_client.post(
        f"/api/organizations/{organization.id}/customers/",
        json={
            "name": "Staff Customer",
            "email": "staff@example.com",
        },
    )

    assert response.status_code == 403


def test_staff_cannot_update_customer(
    staff_authenticated_client,
    organization,
    customer,
):
    response = staff_authenticated_client.patch(
        f"/api/organizations/{organization.id}/customers/{customer.id}",
        json={
            "name": "Updated By Staff",
        },
    )

    assert response.status_code == 403


def test_staff_cannot_delete_customer(
    staff_authenticated_client,
    organization,
    customer,
):
    response = staff_authenticated_client.delete(
        f"/api/organizations/{organization.id}/customers/{customer.id}"
    )

    assert response.status_code == 403