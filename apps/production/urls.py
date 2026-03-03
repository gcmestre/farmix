from django.urls import path

from . import views

app_name = "production"

urlpatterns = [
    path("batches/", views.batch_list, name="batch_list"),
    path("batches/create/", views.batch_create, name="batch_create"),
    path("batches/<uuid:pk>/", views.batch_detail, name="batch_detail"),
    path("batches/<uuid:pk>/pdf/", views.batch_pdf, name="batch_pdf"),
    path("batches/<uuid:pk>/label/", views.batch_label, name="batch_label"),
    path("batches/<uuid:pk>/cost/", views.batch_cost, name="batch_cost"),
    path("batches/<uuid:pk>/status/<str:action>/", views.batch_status_update, name="batch_status_update"),
    path("batches/<uuid:batch_pk>/qc/", views.qc_create, name="qc_create"),
    path("batches/<uuid:batch_pk>/qc/detail/", views.qc_detail, name="qc_detail"),
    path(
        "batches/<uuid:batch_pk>/steps/<uuid:step_pk>/complete/",
        views.batch_step_complete,
        name="batch_step_complete",
    ),
    path("formulations/", views.formulation_list, name="formulation_list"),
    path("formulations/create/", views.formulation_create, name="formulation_create"),
    path("formulations/<uuid:pk>/", views.formulation_detail, name="formulation_detail"),
    path("formulations/<uuid:pk>/edit/", views.formulation_edit, name="formulation_edit"),
    path(
        "formulations/<uuid:formulation_pk>/ingredients/add/",
        views.formulation_add_ingredient,
        name="formulation_add_ingredient",
    ),
    path(
        "formulations/<uuid:formulation_pk>/steps/add/",
        views.formulation_add_step,
        name="formulation_add_step",
    ),
    path("formulations/<uuid:pk>/calculator/", views.batch_calculator, name="batch_calculator"),
    path("calibrations/", views.calibration_list, name="calibration_list"),
    path("calibrations/create/", views.calibration_create, name="calibration_create"),
]
