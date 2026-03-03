from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Address, AuditLog, Consent, Pharmacy, UserProfile


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "nif", "anf_number", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("is_active",)
    search_fields = ("name", "nif", "slug")


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "pharmacy", "user", "action", "model_name", "object_id")
    list_filter = ("action", "model_name", "pharmacy")
    search_fields = ("model_name", "object_id")
    readonly_fields = (
        "id",
        "pharmacy",
        "timestamp",
        "user",
        "action",
        "model_name",
        "object_id",
        "changes",
        "ip_address",
    )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Consent)
class ConsentAdmin(admin.ModelAdmin):
    list_display = ("user", "pharmacy", "purpose", "legal_basis", "granted_at", "revoked_at", "is_active")
    list_filter = ("purpose", "legal_basis", "pharmacy")


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("street", "postal_code", "city", "country")
