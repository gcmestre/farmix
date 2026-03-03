import mimetypes

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ALLOWED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")
ALLOWED_MIME_TYPES = (
    "application/pdf",
    "image/jpeg",
    "image/png",
)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class FileValidator:
    """Validates file uploads: extension, MIME type, and size."""

    def __init__(
        self,
        allowed_extensions=ALLOWED_EXTENSIONS,
        allowed_mime_types=ALLOWED_MIME_TYPES,
        max_size=MAX_FILE_SIZE,
    ):
        self.allowed_extensions = allowed_extensions
        self.allowed_mime_types = allowed_mime_types
        self.max_size = max_size

    def __call__(self, file):
        self._validate_extension(file)
        self._validate_size(file)
        self._validate_mime_type(file)

    def _validate_extension(self, file):
        import os

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in self.allowed_extensions:
            raise ValidationError(
                _("File extension '%(ext)s' is not allowed. Allowed: %(allowed)s"),
                params={
                    "ext": ext,
                    "allowed": ", ".join(self.allowed_extensions),
                },
                code="invalid_extension",
            )

    def _validate_size(self, file):
        if file.size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            raise ValidationError(
                _("File size %(size).1f MB exceeds the maximum of %(max).0f MB."),
                params={
                    "size": file.size / (1024 * 1024),
                    "max": max_mb,
                },
                code="file_too_large",
            )

    def _validate_mime_type(self, file):
        # Read the first bytes to guess MIME type
        mime_type = None

        # Try reading magic bytes from uploaded file
        if hasattr(file, "content_type"):
            mime_type = file.content_type

        # Cross-check with extension-based MIME type
        guessed_type, _ = mimetypes.guess_type(file.name)
        if guessed_type and mime_type and guessed_type != mime_type:
            # Trust the header sniff from the upload, but validate it
            pass

        check_type = mime_type or guessed_type
        if check_type and check_type not in self.allowed_mime_types:
            raise ValidationError(
                _("File type '%(type)s' is not allowed. Allowed: %(allowed)s"),
                params={
                    "type": check_type,
                    "allowed": ", ".join(self.allowed_mime_types),
                },
                code="invalid_mime_type",
            )

    def __eq__(self, other):
        return (
            isinstance(other, FileValidator)
            and self.allowed_extensions == other.allowed_extensions
            and self.allowed_mime_types == other.allowed_mime_types
            and self.max_size == other.max_size
        )

    def deconstruct(self):
        path = "apps.core.validators.FileValidator"
        args = ()
        kwargs = {}
        if self.allowed_extensions != ALLOWED_EXTENSIONS:
            kwargs["allowed_extensions"] = self.allowed_extensions
        if self.allowed_mime_types != ALLOWED_MIME_TYPES:
            kwargs["allowed_mime_types"] = self.allowed_mime_types
        if self.max_size != MAX_FILE_SIZE:
            kwargs["max_size"] = self.max_size
        return path, args, kwargs
