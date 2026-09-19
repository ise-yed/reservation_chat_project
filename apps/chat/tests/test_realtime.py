import uuid
from datetime import timedelta

import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from apps.appointments.enums import AppointmentStatus
from apps.appointments.tests.factories import AppointmentFactory
from apps.chat.middleware import JWTAuthMiddleware
from apps.chat.routing import websocket_urlpatterns
from apps.chat.tests.factories import ConversationFactory
from apps.offerings.enums import VisitMode
from apps.providers.tests.factories import ProviderProfileFactory
from apps.users.tests.factories import UserFactory

# ساخت اپلیکیشنِ اختصاصیِ تست، برای دور زدن 제한ات AllowedHostsOriginValidator
test_application = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

pytestmark = pytest.mark.django_db(transaction=True)


@sync_to_async
def setup_chat_environment():
    """یک محیط چت کامل با نوبت فعال برای تست سوکت می‌سازد"""
    conversation = ConversationFactory()
    provider_profile = ProviderProfileFactory(user=conversation.provider)
    stranger = UserFactory()

    now = timezone.now()
    start_at = now - timedelta(minutes=15)
    end_at = now + timedelta(minutes=15)

    AppointmentFactory(
        customer=conversation.customer,
        provider=provider_profile,
        visit_mode=VisitMode.ONLINE_CHAT,
        status=AppointmentStatus.CONFIRMED,
        start_at=start_at,
        end_at=end_at,
        blocked_start_at=start_at,
        blocked_end_at=end_at,
    )

    return conversation, stranger


@pytest.mark.asyncio
async def test_ws_rejects_anonymous_user():
    """اگر توکن فرستاده نشود، سوکت باید با کد 4001 بسته شود"""
    fake_uuid = uuid.uuid4()

    # استفاده از test_application به جای application اصلی
    communicator = WebsocketCommunicator(
        test_application,
        f"/ws/chat/{fake_uuid}/"
    )

    connected, close_code = await communicator.connect()

    assert connected is False
    assert close_code == 4001  # Unauthorized


@pytest.mark.asyncio
async def test_ws_rejects_stranger():
    """اگر شخص ثالث (با توکن معتبر خودش) بخواهد به چت دیگران وصل شود، باید با کد 4003 رد شود"""
    conversation, stranger = await setup_chat_environment()
    stranger_token = str(AccessToken.for_user(stranger))

    communicator = WebsocketCommunicator(
        test_application,
        f"/ws/chat/{conversation.id}/",
        headers=[
            (b"authorization", f"Bearer {stranger_token}".encode("latin-1"))
        ]
    )

    connected, close_code = await communicator.connect()

    assert connected is False
    assert close_code == 4003  # Forbidden


@pytest.mark.asyncio
async def test_ws_accepts_valid_participant():
    """بیمار مجاز باید بتواند با موفقیت به گروه سوکت خودش متصل شود"""
    conversation, _ = await setup_chat_environment()
    patient_token = str(AccessToken.for_user(conversation.customer))

    communicator = WebsocketCommunicator(
        test_application,
        f"/ws/chat/{conversation.id}/",
        headers=[
            (b"authorization", f"Bearer {patient_token}".encode("latin-1"))
        ]
    )

    connected, subprotocol = await communicator.connect()

    # اتصال باید کاملاً موفق باشد
    assert connected is True
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_ws_typing_broadcast():
    """بیمار باید بتواند وضعیت تایپینگ خود را به سوکت بفرستد و سرور آن را برگرداند"""
    conversation, _ = await setup_chat_environment()
    patient_token = str(AccessToken.for_user(conversation.customer))

    communicator = WebsocketCommunicator(
        test_application,
        f"/ws/chat/{conversation.id}/",
        headers=[
            (b"authorization", f"Bearer {patient_token}".encode("latin-1"))
        ]
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # ارسال رویداد شروع تایپینگ
    await communicator.send_json_to({
        "event": "typing.start",
        "data": {}
    })

    # دریافت پاسخی که سرور به همه (از جمله خود بیمار) برادکست می‌کند
    response = await communicator.receive_json_from()

    assert response["event"] == "typing.changed"
    assert response["data"]["user_id"] == str(conversation.customer.id)
    assert response["data"]["is_typing"] is True

    await communicator.disconnect()

@pytest.mark.asyncio
async def test_ws_reconnect_success():
    """تست قطع عمدی و اتصال مجدد (Reconnect) برای اطمینان از پاکسازی صحیح گروه‌ها"""
    conversation, _ = await setup_chat_environment()
    patient_token = str(AccessToken.for_user(conversation.customer))

    headers = [
        (b"host", b"127.0.0.1"),
        (b"authorization", f"Bearer {patient_token}".encode("latin-1"))
    ]

    # 1. اتصال اولیه
    comm1 = WebsocketCommunicator(test_application, f"/ws/chat/{conversation.id}/", headers=headers)
    connected1, _ = await comm1.connect()
    assert connected1 is True
    await comm1.disconnect()  # قطع ارتباط (شبیه‌سازی قطعی اینترنت)

    # 2. اتصال مجدد (Reconnect)
    comm2 = WebsocketCommunicator(test_application, f"/ws/chat/{conversation.id}/", headers=headers)
    connected2, _ = await comm2.connect()
    assert connected2 is True
    await comm2.disconnect()


@pytest.mark.asyncio
async def test_ws_auth_expired_event():
    """اطمینان از اینکه اگر توکن حین اتصال منقضی شود، سرور رویداد auth.expired را فرستاده و قطع می‌کند"""
    conversation, _ = await setup_chat_environment()

    # ساخت توکنی که فقط 1 ثانیه اعتبار دارد
    token = AccessToken.for_user(conversation.customer)
    token.set_exp(lifetime=timedelta(seconds=1))

    communicator = WebsocketCommunicator(
        test_application,
        f"/ws/chat/{conversation.id}/",
        headers=[
            (b"host", b"127.0.0.1"),
            (b"authorization", f"Bearer {token}".encode("latin-1"))
        ]
    )

    connected, _ = await communicator.connect()
    assert connected is True

    # منتظر می‌مانیم تا سرور متوجه انقضا شود (تسک پس‌زمینه بیدار شود)
    response = await communicator.receive_json_from(timeout=2.0)
    assert response["event"] == "auth.expired"

    # پس از ارسال رویداد، سوکت باید بسته شود
    await communicator.wait()
