import json
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pywebpush import webpush, WebPushException

from app.config import settings
from app.db.session import get_db, SessionLocal
from app.db import models as db_models
from app.services.auth_service import get_current_user

logger = logging.getLogger(__name__)

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
    action_url: Optional[str] = "/"

@router.get("/vapid-public-key")
def get_vapid_public_key():
    """Returns application VAPID public key for Web Push subscription."""
    if not settings.VAPID_PUBLIC_KEY:
        # In development without env var, generate or supply active test key
        return {
            "public_key": "BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBKr3qBUYhHBQFLXYp5NMPH84",
            "is_custom": False,
            "instructions": "Set VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY in environment for production web push."
        }
    return {"public_key": settings.VAPID_PUBLIC_KEY, "is_custom": True}

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
def send_test_push(
    req: PushNotificationSendRequest,
    session: Session = Depends(get_db)
):
    """
    Dispatches a real web push notification using pywebpush to registered browser endpoints.
    """
    if not isinstance(session, Session):
        from app.db.session import SessionLocal
        session = SessionLocal()

    payload_data = json.dumps({
        "title": req.title,
        "body": req.body,
        "icon": req.icon or "/static/icons/icon-192.png",
        "tag": req.tag or "med-reminder",
        "url": req.action_url or "/"
    })

    # Find subscriptions
    query = session.query(db_models.PushSubscription)
    if req.user_id:
        query = query.filter(db_models.PushSubscription.user_id == req.user_id)
    subscriptions = query.all()

    dispatched_count = 0
    if settings.VAPID_PRIVATE_KEY and settings.VAPID_PUBLIC_KEY:
        for sub in subscriptions:
            try:
                subscription_info = {
                    "endpoint": sub.endpoint,
                    "keys": {
                        "p256dh": sub.p256dh,
                        "auth": sub.auth
                    }
                }
                webpush(
                    subscription_info=subscription_info,
                    data=payload_data,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": f"mailto:{settings.VAPID_CLAIMS_EMAIL}"}
                )
                dispatched_count += 1
            except WebPushException as ex:
                logger.warning(f"Web push dispatch failed for {sub.endpoint[:30]}...: {ex}")
            except Exception as e:
                logger.warning(f"Unexpected push error: {e}")

    return {
        "status": "success",
        "dispatched": True,
        "sent_count": dispatched_count,
        "total_subscribers": len(subscriptions),
        "title": req.title,
        "body": req.body,
        "message": f"Push reminder dispatched to {dispatched_count} subscriber(s)."
    }
