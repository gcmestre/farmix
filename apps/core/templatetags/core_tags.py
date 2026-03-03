from django import template

register = template.Library()


@register.filter
def status_color(status):
    """Return TailwindCSS color name for order/batch status."""
    colors = {
        "new_request": "blue",
        "waiting_for_quote": "yellow",
        "waiting_for_recipe": "yellow",
        "ready_for_production": "indigo",
        "in_production": "purple",
        "quality_check": "purple",
        "ready": "green",
        "complete": "green",
        "approved": "green",
        "cancelled": "red",
        "error": "red",
        "rejected": "red",
        "draft": "gray",
        "sent": "blue",
        "paid": "green",
        "overdue": "red",
        "planned": "gray",
        "in_progress": "purple",
    }
    return colors.get(status, "gray")


@register.filter
def has_role(user, role):
    """Check if user has a specific role. Usage: {% if user|has_role:'admin' %}"""
    if getattr(user, "is_superuser", False):
        return True
    try:
        return user.userprofile.role == role
    except Exception:
        return False


@register.filter
def can_manage(user, area):
    """Check if user can manage a specific area. Usage: {% if user|can_manage:'orders' %}"""
    if getattr(user, "is_superuser", False):
        return True
    try:
        profile = user.userprofile
        checks = {
            "orders": profile.can_manage_orders,
            "production": profile.can_manage_production,
            "invoicing": profile.can_manage_invoicing,
        }
        return checks.get(area, False)
    except Exception:
        return False
