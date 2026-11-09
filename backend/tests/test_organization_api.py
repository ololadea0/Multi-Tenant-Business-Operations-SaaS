from app.models.membership import Membership, MembershipRole
from app.models.organization import Organization
from app.models.user import User


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

def test_admin_cannot_update_organization_metadata(
    client,
    organization,
    db,
):
    admin_user = User(
        email="admin@example.com",
        full_name="Admin User",
        password_hash="hashed",
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    admin_membership = Membership(
        user_id=admin_user.id,
        organization_id=organization.id,
        role=MembershipRole.ADMIN,
    )
    db.add(admin_membership)
    db.commit()

    def override_current_user():
        return admin_user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.patch(
        f"/api/organizations/{organization.id}",
        json={
            "name": "Updated by admin",
            "email": "admin@updated.com",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "You do not have permission to perform this action"
    )

    app.dependency_overrides.clear()


def test_member_can_leave_organization(
    client,
    organization,
    db,
):
    member_user = User(
        email="member@example.com",
        full_name="Member User",
        password_hash="hashed",
        is_active=True,
    )
    db.add(member_user)
    db.commit()
    db.refresh(member_user)

    member_membership = Membership(
        user_id=member_user.id,
        organization_id=organization.id,
        role=MembershipRole.STAFF,
    )
    db.add(member_membership)
    db.commit()

    def override_current_user():
        return member_user

    from app.api.dependencies import get_current_user
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user

    response = client.delete(f"/api/organizations/{organization.id}/leave")

    assert response.status_code == 200
    assert response.json()["message"] == "You left the organization"

    remaining_membership = (
        db.query(Membership)
        .filter(
            Membership.organization_id == organization.id,
            Membership.user_id == member_user.id,
        )
        .first()
    )
    assert remaining_membership is None

    app.dependency_overrides.clear()

def test_update_organization_metadata(
    authenticated_client,
    organization,
):
    response = authenticated_client.patch(
        f"/api/organizations/{organization.id}",
        json={
            "name": "Updated Studio",
            "email": "hello@updatedstudio.com",
            "address_line_1": "123 Main Street",
            "city": "Lagos",
            "country": "Nigeria",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Studio"
    assert data["email"] == "hello@updatedstudio.com"
    assert data["address_line_1"] == "123 Main Street"
    assert data["city"] == "Lagos"
    assert data["country"] == "Nigeria"


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