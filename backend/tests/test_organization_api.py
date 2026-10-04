from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization


def test_get_organization(
    authenticated_client,
    organization,
):
    response = authenticated_client.get(
        f"/api/organizations/{organization.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == organization.id
    assert data["name"] == organization.name
    assert data["slug"] == organization.slug
    assert data["role"] == "owner"


def test_get_nonexistent_organization(
    authenticated_client,
):
    response = authenticated_client.get(
        "/api/organizations/999999"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have access to this organization"
    )


def test_get_organization_without_membership(
    client,
    user,
    db,
):
    other_organization = Organization(
        name="Other Organization",
        slug="other-organization",
    )

    db.add(other_organization)
    db.commit()
    db.refresh(other_organization)

    def override_current_user():
        return user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.get(
        f"/api/organizations/{other_organization.id}"
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have access to this organization"
    )

    app.dependency_overrides.clear()


def test_create_organization(
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/organizations/",
        params={
            "name": "New Organization"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "New Organization"
    assert data["slug"].startswith("new-organization-")
    assert data["role"] == "owner"


def test_list_user_organizations(
    authenticated_client,
    organization,
):
    response = authenticated_client.get(
        "/api/organizations/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == organization.id
    assert data[0]["name"] == organization.name
    assert data[0]["role"] == "owner"


def test_staff_can_access_organization(
    staff_authenticated_client,
    organization,
):
    response = staff_authenticated_client.get(
        f"/api/organizations/{organization.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == organization.id
    assert data["role"] == "staff"


def test_staff_organizations_list(
    staff_authenticated_client,
    organization,
):
    response = staff_authenticated_client.get(
        "/api/organizations/"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == organization.id
    assert data[0]["role"] == "staff"