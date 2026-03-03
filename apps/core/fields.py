import base64

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def _get_fernet():
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "")
    if not key:
        raise ValueError("FIELD_ENCRYPTION_KEY is not set in settings.")
    # Accept both raw Fernet key and base64 URL-safe key
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_value(value):
    """Encrypt a string value using Fernet."""
    if not value:
        return value
    f = _get_fernet()
    return f.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value):
    """Decrypt a Fernet-encrypted string value."""
    if not value:
        return value
    f = _get_fernet()
    try:
        return f.decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        # Return raw value if decryption fails (e.g., not yet encrypted)
        return value


class EncryptedCharField(models.CharField):
    """CharField that encrypts data at rest using Fernet."""

    description = _("Encrypted CharField")

    def __init__(self, *args, **kwargs):
        # Encrypted values are longer than plain text; ensure enough DB space
        kwargs.setdefault("max_length", 500)
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs


class EncryptedTextField(models.TextField):
    """TextField that encrypts data at rest using Fernet."""

    description = _("Encrypted TextField")

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, path, args, kwargs
