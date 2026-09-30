from fastapi import APIRouter
from app.api.v1 import auth, users, tickets, categories, comments, attachments, notifications, dashboard, audit

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
api_router.include_router(comments.router, prefix="/tickets", tags=["Comments"])
api_router.include_router(attachments.router, prefix="/tickets", tags=["Attachments"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
