from django.urls import path

from . import views

app_name = "invoicing"

urlpatterns = [
    # Quotes
    path("quotes/", views.quote_list, name="quote_list"),
    path("quotes/create/", views.quote_create, name="quote_create"),
    path("quotes/<uuid:pk>/", views.quote_detail, name="quote_detail"),
    path(
        "quotes/<uuid:quote_pk>/lines/add/",
        views.quote_add_line,
        name="quote_add_line",
    ),
    path(
        "quotes/<uuid:pk>/to-invoice/",
        views.quote_to_invoice,
        name="quote_to_invoice",
    ),
    # Invoices
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/create/", views.invoice_create, name="invoice_create"),
    path("invoices/<uuid:pk>/", views.invoice_detail, name="invoice_detail"),
    path(
        "invoices/<uuid:invoice_pk>/lines/add/",
        views.invoice_add_line,
        name="invoice_add_line",
    ),
    path(
        "invoices/<uuid:pk>/status/<str:action>/",
        views.invoice_status_update,
        name="invoice_status_update",
    ),
    path(
        "invoices/export/csv/",
        views.invoice_export_csv,
        name="invoice_export_csv",
    ),
]
