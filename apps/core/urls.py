from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("register/", views.register, name="register"),
    path("invite/<uuid:token>/", views.invitation_accept, name="invitation_accept"),
    path("profile/", views.profile, name="profile"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
    path("users/<int:pk>/remove/", views.user_remove, name="user_remove"),
    path("users/invite/", views.invitation_create, name="invitation_create"),
    path("users/invitations/", views.invitation_list, name="invitation_list"),
    path("users/invitations/<uuid:pk>/revoke/", views.invitation_revoke, name="invitation_revoke"),
    path("users/invitations/<uuid:pk>/resend/", views.invitation_resend, name="invitation_resend"),
    path("audit-log/", views.audit_log, name="audit_log"),
]
