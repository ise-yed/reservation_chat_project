from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user_and_exp_from_token(token):
    try:
        access_token = AccessToken(token)
        user_id = access_token.get("user_id")
        exp = access_token.get("exp")  # استخراج زمان انقضا (Timestamp)
        return User.objects.get(id=user_id), exp
    except (InvalidToken, TokenError, KeyError, User.DoesNotExist, ValueError):
        return AnonymousUser(), None


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = self._extract_token(scope)

        if token:
            scope["user"], scope["token_exp"] = await get_user_and_exp_from_token(token)
        else:
            scope["user"] = AnonymousUser()
            scope["token_exp"] = None

        return await super().__call__(scope, receive, send)

    def _extract_token(self, scope) -> str | None:
        headers = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers", [])}
        auth_header = headers.get("authorization", "")

        if auth_header.startswith(("Bearer ", "Token ")):
            return auth_header.split(" ", 1)[1]

        query_params = parse_qs(scope.get("query_string", b"").decode())
        return query_params.get("token", [None])[0]
