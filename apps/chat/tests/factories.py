import factory

from apps.chat.enums import MessageType
from apps.chat.models import Conversation, Message
from apps.users.tests.factories import UserFactory


class ConversationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Conversation

    customer = factory.SubFactory(UserFactory, role="customer")
    provider = factory.SubFactory(UserFactory, role="provider")


class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    conversation = factory.SubFactory(ConversationFactory)
    sender = factory.SelfAttribute("conversation.customer")
    type = MessageType.TEXT
    content = factory.Faker("sentence")
    is_deleted = False