from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("create/", views.order_create, name="order_create"),
    path("<uuid:pk>/", views.order_detail, name="order_detail"),
    path("<uuid:pk>/edit/", views.order_edit, name="order_edit"),
    path("<uuid:pk>/status/", views.order_status_update, name="order_status_update"),
    path("<uuid:order_pk>/items/add/", views.order_item_add, name="order_item_add"),
    path("clients/", views.client_list, name="client_list"),
    path("clients/create/", views.client_create, name="client_create"),
    path("clients/autocomplete/", views.client_autocomplete, name="client_autocomplete"),
    path("clients/<uuid:pk>/", views.client_detail, name="client_detail"),
    path("clients/<uuid:pk>/edit/", views.client_edit, name="client_edit"),
    path("export/csv/", views.order_export_csv, name="order_export_csv"),
    path("complaints/", views.complaint_list, name="complaint_list"),
    path("complaints/create/", views.complaint_create, name="complaint_create"),
    path("complaints/<uuid:pk>/", views.complaint_detail, name="complaint_detail"),
]
