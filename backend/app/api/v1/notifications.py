from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class SendAlertRequest(BaseModel):
    recipient_id: int
    title: str
    body: str
    notification_type: str = "GENERAL"
    reference_id: int | None = None
    reference_type: str | None = None


@router.get("/")
async def get_my_notifications(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all notifications for the current user."""
    service = NotificationService(db)
    notifications = await service.get_user_notifications(current_user.id, limit)
    return [
        {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "channel": n.channel.value,
            "status": n.status.value,
            "is_read": n.is_read,
            "notification_type": n.notification_type,
            "created_at": str(n.created_at),
        }
        for n in notifications
    ]


@router.post("/{notification_id}/read", status_code=204)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read."""
    service = NotificationService(db)
    await service.mark_read(notification_id, current_user.id)


@router.post("/send-alert")
async def send_alert(
    request: SendAlertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a push notification alert to a user."""
    service = NotificationService(db)
    notif = await service.send_push(
        recipient_id=request.recipient_id,
        title=request.title,
        body=request.body,
        extra_data={
            "type": request.notification_type,
            "reference_id": request.reference_id,
            "reference_type": request.reference_type,
        },
    )
    return {"notification_id": notif.id, "status": notif.status.value}


@router.put("/fcm-token")
async def update_fcm_token(
    token: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register or update the FCM token for push notifications."""
    from app.repositories.user_repository import UserRepository
    repo = UserRepository(db)
    await repo.update_fcm_token(current_user.id, token)
    return {"updated": True}
