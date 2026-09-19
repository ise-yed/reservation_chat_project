import filetype
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

from apps.chat.enums import MessageType

MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024

ALLOWED_IMAGE_MIMES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_DOC_MIMES = ["application/pdf"]


def validate_and_get_mime_type(file, msg_type: str) -> str:
    if not file:
        return ""

    if msg_type == MessageType.IMAGE and file.size > MAX_IMAGE_SIZE:
        raise ValidationError({"attachment": ["Image size cannot exceed 5 MB."]})
    if msg_type == MessageType.DOCUMENT and file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError({"attachment": ["Document size cannot exceed 10 MB."]})

    file.seek(0)
    file_bytes = file.read(2048)
    file.seek(0)

    kind = filetype.guess(file_bytes)
    if kind is None:
        raise ValidationError({"attachment": ["Unknown file format or corrupted file."]})

    mime = kind.mime

    if msg_type == MessageType.IMAGE:
        if mime not in ALLOWED_IMAGE_MIMES:
            raise ValidationError(
                {"attachment": [f"Format '{mime}' is not supported. Only JPG, PNG, and WEBP are allowed."]}
            )
        
        # --- بررسی ساختاری تصویر با Pillow ---
        try:
            file.seek(0)
            with Image.open(file) as img:
                img.verify()  
            file.seek(0)
        except (UnidentifiedImageError, Exception):
            raise ValidationError({"attachment": ["The uploaded file is not a valid or intact image."]})
            
    elif msg_type == MessageType.DOCUMENT:
        if mime not in ALLOWED_DOC_MIMES:
            raise ValidationError(
                {"attachment": [f"Format '{mime}' is not supported. Only PDF is allowed."]}
            )

    return mime