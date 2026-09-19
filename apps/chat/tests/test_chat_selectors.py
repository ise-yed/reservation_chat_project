import pytest
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import NotFound

from apps.chat.selectors.chat import (
    get_conversation_messages,
    get_conversation_or_raise,
    get_user_conversations,
)
from apps.chat.tests.factories import ConversationFactory, MessageFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestChatSelectors:
    def test_get_user_conversations(self):
        customer = UserFactory()
        conv1 = ConversationFactory(customer=customer)
        conv2 = ConversationFactory(customer=customer)
        ConversationFactory()  # نان‌مربوط

        conversations = get_user_conversations(customer)
        assert conversations.count() == 2
        assert conv1 in conversations
        assert conv2 in conversations

    def test_get_conversation_or_raise_success(self):
        conv = ConversationFactory()
        fetched = get_conversation_or_raise(conv.id, conv.customer)
        assert fetched == conv

    def test_get_conversation_or_raise_not_found(self):
        user = UserFactory()
        import uuid
        with pytest.raises(NotFound):
            get_conversation_or_raise(uuid.uuid4(), user)

    def test_get_conversation_or_raise_unauthorized(self):
        conv = ConversationFactory()
        stranger = UserFactory()
        with pytest.raises(PermissionDenied):
            get_conversation_or_raise(conv.id, stranger)

    def test_get_conversation_messages_ordering(self):
        conv = ConversationFactory()
        msg1 = MessageFactory(conversation=conv)
        msg2 = MessageFactory(conversation=conv)

        messages = get_conversation_messages(conv)
        assert messages.count() == 2
        # باید نزولی بر اساس تاریخ ساخته شدن باشد (نیاز Cursor Pagination)
        assert messages.first() == msg2
        assert messages.last() == msg1
