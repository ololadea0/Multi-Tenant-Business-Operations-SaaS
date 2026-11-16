from fastapi import APIRouter

from app.api.platform_admin.auth import router as auth_router
from app.api.platform_admin.businesses import router as businesses_router
from app.api.platform_admin.dashboard import router as dashboard_router
from app.api.platform_admin.emails import router as emails_router
from app.api.platform_admin.settings import router as settings_router
from app.api.platform_admin.users import router as users_router

router = APIRouter(prefix="/api/admin", tags=["Platform Admin"])

router.include_router(auth_router)
router.include_router(settings_router)
router.include_router(dashboard_router)
router.include_router(emails_router)
router.include_router(users_router)
router.include_router(businesses_router)

__all__ = ["router"]
