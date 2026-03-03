from functools import wraps

from django.core.exceptions import PermissionDenied

from .models import UserProfile


def role_required(*roles):
    """Decorator to restrict view access to specific user roles."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                profile = request.user.userprofile
                if profile.role in roles:
                    return view_func(request, *args, **kwargs)
            except UserProfile.DoesNotExist:
                pass
            raise PermissionDenied

        return _wrapped_view

    return decorator


def pharmacy_required(view_func):
    """Decorator that returns 403 if request.pharmacy is None (for non-superuser views)."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not getattr(request, "pharmacy", None):
            raise PermissionDenied("No pharmacy associated with this account.")
        return view_func(request, *args, **kwargs)

    return _wrapped
