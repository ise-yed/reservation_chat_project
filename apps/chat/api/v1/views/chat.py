from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema_view
from rest_framework import generics, parsers, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.api.v1.docs import (
    conversation_detail_schema,
    conversation_list_schema,
    message_create_schema,
    message_delete_schema,
    message_list_schema,
    update_read_pointer_schema,
)
from apps.chat.api.v1.serializers.chat import (
    ConversationReadSerializer,
    MessageCreateSerializer,
    MessageReadSerializer,
    ReadPointerUpdateSerializer,
)
from apps.chat.models import Message
from apps.chat.selectors.chat import (
    get_conversation_messages,
    get_conversation_or_raise,
    get_user_conversations,
)
from apps.chat.services.messages import (
    delete_message,
    send_message,
    update_read_pointer,
)
from apps.common.pagination import MessageCursorPagination


@extend_schema_view(get=conversation_list_schema)
class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_user_conversations(user=self.request.user)


class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @conversation_detail_schema
    def get(self, request, conversation_id):
        conversation = get_conversation_or_raise(conversation_id, request.user)
        serializer = ConversationReadSerializer(conversation, context={"request": request})
        return Response(serializer.data)


@extend_schema_view(
    get=message_list_schema,
    post=message_create_schema
)
class MessageListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessageCursorPagination
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]
        conversation = get_conversation_or_raise(conversation_id, self.request.user)
        return get_conversation_messages(conversation)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MessageCreateSerializer
        return MessageReadSerializer

    def create(self, request, *args, **kwargs):
        conversation_id = self.kwargs["conversation_id"]
        conversation = get_conversation_or_raise(conversation_id, request.user)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = send_message(
            conversation=conversation,
            sender=request.user,
            msg_type=serializer.validated_data.get("type"),
            content=serializer.validated_data.get("content", ""),
            attachment=serializer.validated_data.get("attachment"),
        )

        output_serializer = MessageReadSerializer(message)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class MessageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @message_delete_schema
    def delete(self, request, message_id):
        message = get_object_or_404(Message.objects.select_related("conversation__provider"), id=message_id)
        delete_message(message=message, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateReadPointerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @update_read_pointer_schema
    def post(self, request, conversation_id):
        conversation = get_conversation_or_raise(conversation_id, request.user)
        serializer = ReadPointerUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        last_read_message = get_object_or_404(Message, id=serializer.validated_data["last_read_message_id"])

        update_read_pointer(
            conversation=conversation,
            user=request.user,
            last_read_message=last_read_message
        )
        return Response({"status": "success"}, status=status.HTTP_200_OK)

