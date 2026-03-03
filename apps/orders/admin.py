from django.contrib import admin

from .models import Client, Order, OrderItem, OrderStatusLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "client_type", "nif", "email", "phone", "pharmacy")
    list_filter = ("client_type", "pharmacy")
    search_fields = ("name", "nif", "email")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "client", "status", "priority", "source", "pharmacy", "created_at")
    list_filter = ("status", "priority", "source", "pharmacy")
    search_fields = ("order_number", "client__name")
    readonly_fields = ("order_number",)
    inlines = [OrderItemInline]


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ("order", "from_status", "to_status", "changed_by", "timestamp")
    readonly_fields = ("order", "from_status", "to_status", "changed_by", "comment", "timestamp")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
