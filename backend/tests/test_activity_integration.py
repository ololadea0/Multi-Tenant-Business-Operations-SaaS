from app.models.activity import Activity
from app.models.customer import Customer
from app.models.user import User
from app.services.activity import create_activity
from app.core.security import hash_password


def test_order_creation_creates_activity_record(
    authenticated_client,
    db,
    organization,
    product,
):
    customer = Customer(
        organization_id=organization.id,
        name="Order Customer",
        email="order.customer@mail.test",
        phone="08000000001",
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

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

    activities = db.query(Activity).filter(
        Activity.organization_id == organization.id,
        Activity.action == "order.created",
    ).all()

    assert len(activities) == 1
    assert activities[0].entity_id is not None


def test_add_member_creates_activity_record(
    authenticated_client,
    db,
    organization,
):
    new_user = User(
        email="member.activity@test.com",
        full_name="Member Activity",
        password_hash=hash_password("TestPassword123!"),
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/members/",
        json={
            "user_id": new_user.id,
            "role": "staff",
        },
    )

    assert response.status_code == 200

    activities = db.query(Activity).filter(
        Activity.organization_id == organization.id,
        Activity.action == "member.added",
    ).all()

    assert len(activities) == 1
    assert activities[0].entity_id == new_user.id


def test_invitation_creation_creates_activity_record(
    authenticated_client,
    db,
    organization,
    user,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.invitation.send_organization_invitation_email",
        lambda **kwargs: None,
    )

    response = authenticated_client.post(
        f"/api/organizations/{organization.id}/invitations/",
        json={
            "email": "invitee@resend.dev",
            "role": "staff",
        },
    )

    assert response.status_code == 200

    activities = db.query(Activity).filter(
        Activity.organization_id == organization.id,
        Activity.action == "invitation.created",
    ).all()

    assert len(activities) == 1
    assert activities[0].user_id == user.id


def test_activity_service_rollback_discards_uncommitted_record(db, organization, user):
    create_activity(
        db=db,
        organization_id=organization.id,
        user_id=user.id,
        action="activity.rollback_test",
        entity_type="product",
        entity_id=1,
        description="This should be rolled back",
    )

    assert db.query(Activity).filter(Activity.action == "activity.rollback_test").count() == 1

    db.rollback()

    assert db.query(Activity).filter(Activity.action == "activity.rollback_test").count() == 0
