from django.db import models


class VisitMode(models.TextChoices):
    IN_PERSON = "in_person", "In Person"
    ONLINE_CHAT = "online_chat", "Online Chat"
