from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """Authenticate using email address instead of username."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(
                email__iexact=username,
                is_active=True,
            ).first()
            if user is None:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
