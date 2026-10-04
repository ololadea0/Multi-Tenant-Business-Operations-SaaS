from app.models.user import User
from app.models.membership import Membership, MembershipRole
from app.core.security import hash_password


def create_user(db, email, full_name="Test Member"):
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


def test_owner_can_add_member(
    authenticated_client,
    db,
    organization,
):
    new_user = create_user(
        db,
        "member@example.com",
        "New Member",
    )

    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/members/",
        json={
            "user_id": new_user.id,
            "role": "staff",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Member added successfully"
    assert data["user_id"] == new_user.id
    assert data["organization_id"] == organization.id
    assert data["role"] == "staff"


def test_cannot_add_nonexistent_user(
    authenticated_client,
    organization,
):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/members/",
        json={
            "user_id": 99999,
            "role": "staff",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_cannot_add_existing_member(
    authenticated_client,
    user,
    organization,
):
    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/members/",
        json={
            "user_id": user.id,
            "role": "staff",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "User is already a member of this organization"
    )


def test_cannot_add_owner_role(
    authenticated_client,
    db,
    organization,
):
    new_user = create_user(
        db,
        "owner-test@example.com",
        "Owner Test",
    )

    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/members/",
        json={
            "user_id": new_user.id,
            "role": "owner",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Use the ownership transfer flow to assign ownership"
    )


def test_staff_cannot_add_member(
    staff_authenticated_client,
    db,
    organization,
):
    new_user = create_user(
        db,
        "staff-target@example.com",
        "Staff Target",
    )

    response = staff_authenticated_client.post(
        f"/api/organizations/{organization.id}/members/",
        json={
            "user_id": new_user.id,
            "role": "staff",
        },
    )

    assert response.status_code == 403


def test_owner_can_update_member_role(
    authenticated_client,
    db,
    organization,
):
    new_user = create_user(
        db,
        "role-change@example.com",
        "Role Change",
    )

    membership = Membership(
        user_id=new_user.id,
        organization_id=organization.id,
        role=MembershipRole.STAFF,
    )

    db.add(membership)
    db.commit()

    response = authenticated_client.patch(
        f"/api/organizations/{organization.id}/members/{new_user.id}",
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Member role updated successfully"
    assert data["user_id"] == new_user.id
    assert data["role"] == "manager"


def test_cannot_update_nonexistent_member(
    authenticated_client,
    organization,
):
    response = authenticated_client.patch(
        f"/api/organizations/{organization.id}/members/99999",
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


def test_cannot_change_owner_role(
    authenticated_client,
    user,
    organization,
):
    response = authenticated_client.patch(
        f"/api/organizations/{organization.id}/members/{user.id}",
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Owner role cannot be changed here"
    )


def test_cannot_assign_owner_role(
    authenticated_client,
    db,
    organization,
):
    new_user = create_user(
        db,
        "owner-role@example.com",
        "Owner Role",
    )

    membership = Membership(
        user_id=new_user.id,
        organization_id=organization.id,
        role=MembershipRole.STAFF,
    )

    db.add(membership)
    db.commit()

    response = authenticated_client.patch(
        f"/api/organizations/{organization.id}/members/{new_user.id}",
        json={
            "role": "owner",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Use the ownership transfer flow to assign ownership"
    )


def test_staff_cannot_update_member_role(
    staff_authenticated_client,
    staff_user,
    organization,
):
    response = staff_authenticated_client.patch(
        f"/api/organizations/{organization.id}/members/{staff_user.id}",
        json={
            "role": "manager",
        },
    )

    assert response.status_code == 403


def test_owner_can_remove_member(
    authenticated_client,
    db,
    organization,
):
    new_user = create_user(
        db,
        "remove@example.com",
        "Remove Me",
    )

    membership = Membership(
        user_id=new_user.id,
        organization_id=organization.id,
        role=MembershipRole.STAFF,
    )

    db.add(membership)
    db.commit()

    response = authenticated_client.delete(
        f"/api/organizations/{organization.id}/members/{new_user.id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Member removed successfully"

    removed_membership = db.query(Membership).filter(
        Membership.organization_id == organization.id,
        Membership.user_id == new_user.id,
    ).first()

    assert removed_membership is None


def test_cannot_remove_nonexistent_member(
    authenticated_client,
    organization,
):
    response = authenticated_client.delete(
        f"/api/organizations/{organization.id}/members/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"


def test_cannot_remove_owner(
    authenticated_client,
    user,
    organization,
):
    response = authenticated_client.delete(
        f"/api/organizations/{organization.id}/members/{user.id}"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "The organization owner cannot be removed"
    )


def test_staff_cannot_remove_member(
    staff_authenticated_client,
    db,
    organization,
):
    new_user = create_user(
        db,
        "remove-target@example.com",
        "Remove Target",
    )

    membership = Membership(
        user_id=new_user.id,
        organization_id=organization.id,
        role=MembershipRole.STAFF,
    )

    db.add(membership)
    db.commit()

    response = staff_authenticated_client.delete(
        f"/api/organizations/{organization.id}/members/{new_user.id}"
    )

    assert response.status_code == 403