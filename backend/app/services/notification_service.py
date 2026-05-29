from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.models.notification import Notification, NotificationChannel, NotificationStatus, NotificationPriority


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_push(self, recipient_id: int, title: str, body: str, extra_data: dict = {}) -> Notification:
        notif = Notification(
            recipient_id=recipient_id,
            title=title,
            body=body,
            channel=NotificationChannel.PUSH,
            notification_type=extra_data.get("type", "GENERAL"),
            extra_data=extra_data,
        )
        self.db.add(notif)
        await self.db.flush()

        # In production: await firebase_service.send(recipient_fcm_token, title, body)
        notif.status = NotificationStatus.SENT
        notif.sent_at = datetime.now(timezone.utc)
        await self.db.flush()
        return notif

    async def send_whatsapp(self, phone: str, message: str, recipient_id: int) -> Notification:
        notif = Notification(
            recipient_id=recipient_id,
            title="WhatsApp Message",
            body=message,
            channel=NotificationChannel.WHATSAPP,
        )
        self.db.add(notif)
        await self.db.flush()

        # In production: await twilio_service.send_whatsapp(phone, message)
        notif.status = NotificationStatus.SENT
        notif.sent_at = datetime.now(timezone.utc)
        await self.db.flush()
        return notif

    async def send_attendance_alert(self, parent_id: int, student_name: str, status: str, date_str: str) -> None:
        message = (
            f"Dear Parent, {student_name}'s attendance status for {date_str} is: {status}. "
            "Please contact the school for more information."
        )
        await self.send_push(
            recipient_id=parent_id,
            title="Attendance Alert",
            body=message,
            extra_data={"type": "ATTENDANCE_ALERT"},
        )

    async def send_dropout_risk_alert(self, hm_id: int, student_name: str, risk_score: float) -> None:
        message = (
            f"AI Alert: Student {student_name} has a dropout risk score of {risk_score:.0%}. "
            "Immediate intervention recommended."
        )
        await self.send_push(
            recipient_id=hm_id,
            title="Dropout Risk Alert",
            body=message,
            extra_data={"type": "DROPOUT_RISK", "priority": "HIGH"},
        )

    async def get_user_notifications(self, user_id: int, limit: int = 20) -> list[Notification]:
        from sqlalchemy import select
        result = await self.db.execute(
            select(Notification)
            .where(Notification.recipient_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_read(self, notification_id: int, user_id: int) -> None:
        from sqlalchemy import select
        result = await self.db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_id == user_id,
            )
        )
        notif = result.scalar_one_or_none()
        if notif:
            notif.is_read = True
            notif.read_at = datetime.now(timezone.utc)
            notif.status = NotificationStatus.READ
            await self.db.flush()
