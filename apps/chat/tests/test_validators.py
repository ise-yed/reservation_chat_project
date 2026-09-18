import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.exceptions import ValidationError

from apps.chat.enums import MessageType
from apps.chat.validators import validate_and_get_mime_type

# Real Magic Bytes for testing
VALID_JPEG_BYTES = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x60\x00\x60\x00\x00"
VALID_PDF_BYTES = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n"
MALICIOUS_EXE_BYTES = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00\xb8\x00\x00\x00"


class TestFileValidators:
    def test_valid_image_passes(self):
        file = SimpleUploadedFile("test.jpg", VALID_JPEG_BYTES, content_type="image/jpeg")
        mime = validate_and_get_mime_type(file, MessageType.IMAGE)
        assert mime == "image/jpeg"

    def test_valid_pdf_passes(self):
        file = SimpleUploadedFile("test.pdf", VALID_PDF_BYTES, content_type="application/pdf")
        mime = validate_and_get_mime_type(file, MessageType.DOCUMENT)
        assert mime == "application/pdf"

    def test_image_size_limit(self):
        # 5MB + 1 byte
        file = SimpleUploadedFile("large.jpg", b"0" * ((5 * 1024 * 1024) + 1))
        with pytest.raises(ValidationError, match="Image size cannot exceed"):
            validate_and_get_mime_type(file, MessageType.IMAGE)

    def test_document_size_limit(self):
        # 10MB + 1 byte
        file = SimpleUploadedFile("large.pdf", b"0" * ((10 * 1024 * 1024) + 1))
        with pytest.raises(ValidationError, match="Document size cannot exceed"):
            validate_and_get_mime_type(file, MessageType.DOCUMENT)

    def test_file_spoofing_prevented(self):
        # An EXE malware disguised as a PDF
        file = SimpleUploadedFile("fake_document.pdf", MALICIOUS_EXE_BYTES, content_type="application/pdf")
        with pytest.raises(ValidationError, match="is not supported. Only PDF is allowed"):
            validate_and_get_mime_type(file, MessageType.DOCUMENT)

    def test_unknown_format_rejected(self):
        file = SimpleUploadedFile("unknown.bin", b"random garbage bytes that mean nothing")
        with pytest.raises(ValidationError, match="Unknown file format or corrupted file"):
            validate_and_get_mime_type(file, MessageType.DOCUMENT)

    def test_image_sent_as_document_rejected(self):
        file = SimpleUploadedFile("image_as_doc.jpg", VALID_JPEG_BYTES)
        with pytest.raises(ValidationError, match="Format 'image/jpeg' is not supported. Only PDF is allowed"):
            validate_and_get_mime_type(file, MessageType.DOCUMENT)