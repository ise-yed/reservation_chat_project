from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

from rest_framework.pagination import CursorPagination


class MessageCursorPagination(CursorPagination):
    """Cursor pagination specifically for chat messages (ordered by creation time)."""
    page_size = 30
    ordering = "-created_at"
    cursor_query_param = "cursor"
