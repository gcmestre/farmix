from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("materials/", views.material_list, name="material_list"),
    path("materials/create/", views.material_create, name="material_create"),
    path("materials/<uuid:pk>/", views.material_detail, name="material_detail"),
    path("materials/<uuid:pk>/edit/", views.material_edit, name="material_edit"),
    path("lots/", views.lot_list, name="lot_list"),
    path("lots/create/", views.lot_create, name="lot_create"),
    path("lots/<uuid:pk>/", views.lot_detail, name="lot_detail"),
    path("lots/<uuid:pk>/adjust/", views.lot_adjust, name="lot_adjust"),
    path("suppliers/", views.supplier_list, name="supplier_list"),
    path("suppliers/create/", views.supplier_create, name="supplier_create"),
    path("suppliers/<uuid:pk>/", views.supplier_detail, name="supplier_detail"),
    path("suppliers/<uuid:pk>/edit/", views.supplier_edit, name="supplier_edit"),
    path("lots/<uuid:pk>/release/", views.lot_release, name="lot_release"),
    path("alerts/", views.alerts, name="alerts"),
    path("movements/", views.movements, name="movements"),
    path("export/csv/", views.inventory_export_csv, name="inventory_export_csv"),
    path("prohibited/", views.prohibited_list, name="prohibited_list"),
    path("prohibited/create/", views.prohibited_create, name="prohibited_create"),
    path("prohibited/<uuid:pk>/edit/", views.prohibited_edit, name="prohibited_edit"),
    path("prohibited/<uuid:pk>/delete/", views.prohibited_delete, name="prohibited_delete"),
]
