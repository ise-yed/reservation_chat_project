from django.urls import path

from apps.chat.api.v1.views.chat import (
    ConversationDetailView,
    ConversationListView,
    MessageDetailView,
    MessageListCreateView,
    UpdateReadPointerView,
)

app_name = "chat"

urlpatterns = [
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/<uuid:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<uuid:conversation_id>/messages/", MessageListCreateView.as_view(), name="message-list-create"),
    path("conversations/<uuid:conversation_id>/read/", UpdateReadPointerView.as_view(), name="update-read-pointer"),
    
    path("messages/<uuid:message_id>/", MessageDetailView.as_view(), name="message-detail"),
]