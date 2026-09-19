from django.db import models


class MessageType(models.TextChoices):
    TEXT = "text", "Text"
    IMAGE = "image", "Image"
    DOCUMENT = "document", "Document"
    VOICE = "voice", "Voice"
