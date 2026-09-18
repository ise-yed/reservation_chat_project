import filetype
from rest_framework.exceptions import ValidationError

from apps.chat.enums import MessageType

# Size limits
MAX_IMAGE_SIZE = 5 * 1024 * 1024     # 5 MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024 # 10 MB

# Allowed MIME types
ALLOWED_IMAGE_MIMES = ["image/jpeg", "image/png", "image/webp"]
ALLOWED_DOC_MIMES = ["application/pdf"]


def validate_and_get_mime_type(file, msg_type: str) -> str:
    """
    Validates file size and extracts the true MIME type by inspecting file headers (magic bytes).
    Prevents file extension spoofing (e.g., renaming a .exe to .pdf).
    """
    if not file:
        return ""

    # 1. Size Validation
    if msg_type == MessageType.IMAGE and file.size > MAX_IMAGE_SIZE:
        raise ValidationError({"attachment": ["Image size cannot exceed 5 MB."]})
    if msg_type == MessageType.DOCUMENT and file.size > MAX_DOCUMENT_SIZE:
        raise ValidationError({"attachment": ["Document size cannot exceed 10 MB."]})

    # 2. True MIME Type Extraction
    file.seek(0)
    file_bytes = file.read(2048)
    file.seek(0)  # Reset pointer for downstream saving

    kind = filetype.guess(file_bytes)
    
    if kind is None:
        raise ValidationError({"attachment": ["Unknown file format or corrupted file."]})

    mime = kind.mime

    # 3. Allow-list Validation
    if msg_type == MessageType.IMAGE:
        if mime not in ALLOWED_IMAGE_MIMES:
            raise ValidationError(
                {"attachment": [f"Format '{mime}' is not supported. Only JPG, PNG, and WEBP are allowed."]}
            )
    elif msg_type == MessageType.DOCUMENT:
        if mime not in ALLOWED_DOC_MIMES:
            raise ValidationError(
                {"attachment": [f"Format '{mime}' is not supported. Only PDF is allowed."]}
            )

    return mime