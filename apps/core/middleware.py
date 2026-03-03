import threading

from django.utils.deprecation import MiddlewareMixin

_thread_locals = threading.local()


def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_thread_locals, "user", None)


def get_current_pharmacy():
    """Get the current pharmacy from thread-local storage."""
    return getattr(_thread_locals, "pharmacy", None)


class CurrentUserMiddleware(MiddlewareMixin):
    """Store the current authenticated user in thread-local storage for audit trails."""

    def process_request(self, request):
        _thread_locals.user = request.user if request.user.is_authenticated else None

    def process_response(self, request, response):
        _thread_locals.user = None
        return response


class PharmacyMiddleware(MiddlewareMixin):
    """Resolve the current pharmacy from the authenticated user and store in request + thread-local."""

    def process_request(self, request):
        request.pharmacy = None

        if request.user.is_authenticated:
            if request.user.is_superuser:
                pharmacy_id = request.session.get("current_pharmacy_id")
                if pharmacy_id:
                    from apps.core.models import Pharmacy

                    request.pharmacy = Pharmacy.objects.filter(pk=pharmacy_id, is_active=True).first()
            else:
                try:
                    request.pharmacy = request.user.userprofile.pharmacy
                except Exception:
                    request.pharmacy = None

        _thread_locals.pharmacy = request.pharmacy

    def process_response(self, request, response):
        _thread_locals.pharmacy = None
        return response
