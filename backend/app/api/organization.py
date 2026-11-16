from app.api.platform_organization import (
    create_organization,
    get_organization,
    get_user_membership,
    get_user_organizations,
    leave_organization,
    require_roles,
    router,
    slugify_organization_name,
    update_organization,
)

__all__ = [
    "router",
    "slugify_organization_name",
    "get_user_membership",
    "require_roles",
    "get_organization",
    "update_organization",
    "create_organization",
    "get_user_organizations",
    "leave_organization",
]

# @router.delete("/{organization_id}")
# def delete_organization(
#     organization_id: int,
#     membership: Membership = Depends(
#         require_roles(MembershipRole.OWNER)
#     ),
#     db: Session = Depends(get_db)
# ):
#     organization = db.query(Organization).filter(
#         Organization.id == organization_id
#     ).first()

#     if not organization:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Organization not found"
#         )

#     db.delete(organization)
#     db.commit()

#     return {
#         "message": "Organization deleted successfully"
#     }
