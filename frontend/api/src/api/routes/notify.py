from datetime import datetime, timezone
from fastapi import APIRouter
from src.domain.models import NotificationRequest
from src.services.notification import NotificationService

router = APIRouter(prefix="/notify", tags=["Notifications"])
notification_service = NotificationService()


@router.post("")
async def send_notification(payload: NotificationRequest):
    msg_id = await notification_service.send_audit_summary(
        recipient=payload.recipient,
        document_name=payload.document_name,
        summary=payload.summary,
    )
    return {
        "success": bool(msg_id),
        "data": {"message_id": msg_id},
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": "/api/v1/notify",
        },
    }
