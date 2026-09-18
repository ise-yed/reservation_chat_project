import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# ۱. اپلیکیشن پایه جنگو اول باید لود شود تا خطای AppRegistryNotReady ندهد
django_asgi_app = get_asgi_application()

# ۲. پس از لود شدن جنگو، ماژول‌های چنلز و مسیرهای خودمان را ایمپورت می‌کنیم
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from apps.chat.middleware import JWTAuthMiddleware
from apps.chat.routing import websocket_urlpatterns

# ۳. تفکیک ترافیک HTTP از WebSocket
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})