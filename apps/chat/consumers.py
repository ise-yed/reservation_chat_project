import asyncio
import json
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.chat.models import Message
from apps.chat.selectors.chat import get_conversation_or_raise
from apps.chat.services.messages import update_read_pointer
from apps.chat.services.permissions import can_send_message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or self.user.is_anonymous:
            await self.close(code=4001)
            return

        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]

        try:
            self.conversation = await self._get_conversation()
        except Exception:
            await self.close(code=4003)
            return

        self.group_name = f"conversation_{self.conversation_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # استارت کردن تایمر پس‌زمینه برای انقضای توکن (الزام سند V4)
        token_exp = self.scope.get("token_exp")
        if token_exp:
            self.expiration_task = asyncio.create_task(self._watch_token_expiration(token_exp))

    async def disconnect(self, close_code):
        # توقف تایمر در صورت قطع شدن زودترِ کاربر
        if hasattr(self, "expiration_task"):
            self.expiration_task.cancel()

        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def _watch_token_expiration(self, exp_timestamp):
        """پس از پایان زمان اعتبار توکن، رویداد auth.expired می‌فرستد و قطع می‌کند"""
        now = time.time()
        sleep_time = exp_timestamp - now

        if sleep_time > 0:
            await asyncio.sleep(sleep_time)

        # ارسال رویداد صریح به فلاتر
        await self.send(text_data=json.dumps({
            "event": "auth.expired",
            "data": {}
        }))
        await self.close(code=4001)

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)
            event_name = payload.get("event")
            data = payload.get("data", {})
        except json.JSONDecodeError:
            return

        handler = self.INCOMING_HANDLERS.get(event_name)
        if handler:
            await handler(self, data)

    # ... (متدهای _handle_typing_start، _handle_typing_stop و _handle_seen دقیقاً مثل قبل هستند)
    async def _handle_typing_start(self, data):
        await self._broadcast_typing(is_typing=True)

    async def _handle_typing_stop(self, data):
        await self._broadcast_typing(is_typing=False)

    async def _handle_seen(self, data):
        message_id = data.get("message_id")
        if message_id:
            await self._update_read_pointer_in_db(message_id)

    INCOMING_HANDLERS = {
        "typing.start": _handle_typing_start,
        "typing.stop": _handle_typing_stop,
        "message.seen": _handle_seen,
    }

    async def _broadcast_typing(self, is_typing: bool):
        has_permission = await self._check_send_permission()
        if not has_permission:
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_event",
                "event": "typing.changed",
                "data": {
                    "user_id": str(self.user.id),
                    "is_typing": is_typing,
                },
            },
        )

    async def chat_event(self, event):
        await self.send(text_data=json.dumps({
            "event": event["event"],
            "data": event["data"]
        }))

    @database_sync_to_async
    def _get_conversation(self):
        return get_conversation_or_raise(self.conversation_id, self.user)

    @database_sync_to_async
    def _check_send_permission(self):
        return can_send_message(conversation=self.conversation, user=self.user)

    @database_sync_to_async
    def _update_read_pointer_in_db(self, message_id):
        try:
            msg = Message.objects.get(id=message_id)
            update_read_pointer(conversation=self.conversation, user=self.user, last_read_message=msg)

            from apps.chat.services.realtime import broadcast_read_receipt
            broadcast_read_receipt(
                conversation_id=self.conversation.id,
                user_id=self.user.id,
                last_read_message_id=msg.id
            )
        except Message.DoesNotExist:
            pass
