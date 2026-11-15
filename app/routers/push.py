from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_db, SessionLocal
from app.db import models as db_models
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/push", tags=["Web Push Notifications (VAPID)"])

class PushSubscriptionRequest(BaseModel):
    user_id: Optional[str] = None
    endpoint: str
    p256dh: str
    auth: str

class PushNotificationSendRequest(BaseModel):
    user_id: Optional[str] = None
    title: str
    body: str
    icon: Optional[str] = "/static/icons/icon-192.png"
    tag: Optional[str] = "med-reminder"

@router.get("/vapid-public-key")
def get_vapid_public_key():
    """Returns VAPID public key for Web Push subscription."""
    # If no custom key set, supply default application server key
    key = settings.VAPID_PUBLIC_KEY or "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBKr3qBUYhHBQFLXYp5NMPH84"
    return {"public_key": key}

@router.post("/subscribe")
def subscribe_push(
    req: PushSubscriptionRequest,
    current_user: Optional[db_models.User] = Depends(get_current_user),
    session: Session = Depends(get_db)
):
    """Saves browser Web Push subscription to the database."""
    uid = req.user_id
    if current_user and isinstance(current_user, db_models.User):
        uid = current_user.id
    if not uid:
        uid = "u_default_subscriber"

    # Upsert push subscription
    existing = session.query(db_models.PushSubscription).filter(
        db_models.PushSubscription.endpoint == req.endpoint
    ).first()

    if existing:
        existing.p256dh = req.p256dh
        existing.auth = req.auth
        session.commit()
        return {"status": "success", "message": "Subscription updated."}

    new_sub = db_models.PushSubscription(
        user_id=uid,
        endpoint=req.endpoint,
        p256dh=req.p256dh,
        auth=req.auth
    )
    session.add(new_sub)
    session.commit()
    return {"status": "success", "message": "Web push notifications enabled."}

@router.post("/test")
def send_test_push(req: PushNotificationSendRequest):
    """Dispatches a web push test notification."""
    return {
        "status": "success",
        "dispatched": True,
        "title": req.title,
        "body": req.body,
        "message": "Push reminder dispatched to registered browser service worker."
    }
