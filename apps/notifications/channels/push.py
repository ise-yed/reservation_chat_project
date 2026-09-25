import logging

import firebase_admin
from firebase_admin import messaging
from django.conf import settings
from apps.notifications.channels.base import BaseNotificationChannel
from apps.notifications.models import FCMDevice

logger = logging.getLogger(__name__)

# وقتی کلید فایربیس گرفتید این کدها را از کامنت در بیاورید:
if not firebase_admin._apps:
    cred = firebase_admin.credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)

class PushChannel(BaseNotificationChannel):
    """کانال ارسال نوتیفیکیشن موبایل از طریق FCM"""

    def send(self, recipient: str, subject: str, body: str, **kwargs) -> None:
        # در سیستم ما، recipient آیدی کاربر (User ID) است.
        devices = FCMDevice.objects.filter(user_id=recipient, is_active=True)
        if not devices.exists():
            return

        data_payload = kwargs.get("data", {})
        string_data = {str(k): str(v) for k, v in data_payload.items()}

        for device in devices:
            logger.info(f"PUSH SENT to Device {device.registration_id} | Title: {subject} | Body: {body}")
            try:
                message = messaging.Message(
                    notification=messaging.Notification(title=subject, body=body),
                    data=string_data,
                    token=device.registration_id,
                )
                messaging.send(message)
            except Exception as e:
                logger.error(f"FCM Error for token {device.registration_id}: {e}")

    def validate_recipient(self, recipient: str) -> bool:
        return bool(recipient)
