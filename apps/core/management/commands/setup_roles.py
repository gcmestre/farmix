from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

ROLE_PERMISSIONS = {
    "admin": None,  # All permissions
    "pharmacist": {
        "core": ["view_userprofile", "view_auditlog"],
        "orders": "__all__",
        "production": "__all__",
        "inventory": ["view_rawmaterial", "view_lot", "change_lot", "view_supplier", "view_stockmovement"],
        "invoicing": "__all__",
    },
    "lab_technician": {
        "orders": ["view_order", "view_orderitem", "view_client"],
        "production": "__all__",
        "inventory": ["view_rawmaterial", "view_lot", "view_stockmovement"],
    },
    "front_desk": {
        "orders": [
            "add_order",
            "change_order",
            "view_order",
            "add_orderitem",
            "change_orderitem",
            "view_orderitem",
            "add_client",
            "change_client",
            "view_client",
        ],
        "production": ["view_productionbatch", "view_formulation"],
        "inventory": ["view_rawmaterial", "view_lot"],
        "invoicing": ["view_quote", "view_invoice"],
    },
    "viewer": {
        "orders": ["view_order", "view_orderitem", "view_client"],
        "production": ["view_productionbatch", "view_formulation"],
        "inventory": ["view_rawmaterial", "view_lot", "view_supplier"],
        "invoicing": ["view_quote", "view_invoice"],
    },
}


class Command(BaseCommand):
    help = "Create default user groups/roles with permissions"

    def handle(self, *args, **options):
        for role_name, perm_map in ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=role_name)
            action = "Created" if created else "Updated"

            if perm_map is None:
                # Admin gets all permissions
                group.permissions.set(Permission.objects.all())
                self.stdout.write(f"  {action} group '{role_name}' with ALL permissions")
                continue

            perms = []
            for app_label, codenames in perm_map.items():
                if codenames == "__all__":
                    perms.extend(Permission.objects.filter(content_type__app_label=app_label))
                else:
                    perms.extend(
                        Permission.objects.filter(
                            content_type__app_label=app_label,
                            codename__in=codenames,
                        )
                    )

            group.permissions.set(perms)
            self.stdout.write(f"  {action} group '{role_name}' with {len(perms)} permissions")

        self.stdout.write(self.style.SUCCESS("Role setup complete."))
