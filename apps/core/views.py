from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from .decorators import role_required
from .forms import (
    InvitationForm,
    InvitedUserRegistrationForm,
    PharmacyRegistrationForm,
    UserCreateForm,
    UserEditForm,
    UserProfileForm,
)
from .models import AuditLog, Invitation, UserProfile


def register(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")
    if request.method == "POST":
        form = PharmacyRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="apps.core.backends.EmailBackend")
            messages.success(request, _("Registration successful! Welcome to Farmix."))
            return redirect("core:dashboard")
    else:
        form = PharmacyRegistrationForm()
    return render(request, "registration/register.html", {"form": form, "title": _("Register")})


@login_required
def dashboard(request):
    context = {
        "title": _("Dashboard"),
    }

    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return render(request, "core/dashboard.html", context)

    pharmacy = getattr(request, "pharmacy", None)

    # Order stats
    if profile.role in (
        UserProfile.Role.ADMIN,
        UserProfile.Role.PHARMACIST,
        UserProfile.Role.FRONT_DESK,
    ):
        from apps.orders.models import Order

        order_qs = Order.objects.all()
        if pharmacy:
            order_qs = order_qs.filter(pharmacy=pharmacy)
        context["pending_orders"] = order_qs.filter(
            status__in=["new_request", "waiting_for_quote", "waiting_for_recipe"]
        ).count()
        context["in_production"] = order_qs.filter(status="in_production").count()

    # Inventory alerts
    if profile.role in (UserProfile.Role.ADMIN, UserProfile.Role.PHARMACIST):
        from apps.inventory.services import AlertService

        context["low_stock_count"] = len(AlertService.get_low_stock_materials(pharmacy=pharmacy))
        context["expiring_lots_count"] = AlertService.get_expiring_lots(pharmacy=pharmacy, days=30).count()

    # Invoice stats
    if profile.role in (UserProfile.Role.ADMIN, UserProfile.Role.PHARMACIST):
        from apps.invoicing.models import Invoice

        invoice_qs = Invoice.objects.all()
        if pharmacy:
            invoice_qs = invoice_qs.filter(pharmacy=pharmacy)
        context["unpaid_invoices"] = invoice_qs.filter(status__in=["sent", "overdue"]).count()

    return render(request, "core/dashboard.html", context)


@login_required
def profile(request):
    profile_obj, _created = UserProfile.objects.get_or_create(
        user=request.user, defaults={"role": UserProfile.Role.VIEWER}
    )
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully."))
            return redirect("core:profile")
    else:
        form = UserProfileForm(instance=profile_obj)

    return render(request, "core/profile.html", {"form": form, "title": _("My Profile")})


@login_required
@role_required("admin")
def user_list(request):
    users = User.objects.select_related("userprofile").order_by("username")
    pharmacy = getattr(request, "pharmacy", None)
    if pharmacy:
        users = users.filter(userprofile__pharmacy=pharmacy)
    return render(request, "core/user_list.html", {"users": users, "title": _("Users")})


@login_required
@role_required("admin")
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST, pharmacy=getattr(request, "pharmacy", None))
        if form.is_valid():
            form.save()
            messages.success(request, _("User created successfully."))
            return redirect("core:user_list")
    else:
        form = UserCreateForm(pharmacy=getattr(request, "pharmacy", None))

    return render(request, "core/user_form.html", {"form": form, "title": _("Create User")})


@login_required
@role_required("admin")
def user_edit(request, pk):
    pharmacy = getattr(request, "pharmacy", None)
    qs = User.objects.all()
    if pharmacy:
        qs = qs.filter(userprofile__pharmacy=pharmacy)
    user = get_object_or_404(qs, pk=pk)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user, pharmacy=pharmacy)
        if form.is_valid():
            form.save()
            messages.success(request, _("User updated successfully."))
            return redirect("core:user_list")
    else:
        form = UserEditForm(instance=user, pharmacy=pharmacy)

    return render(request, "core/user_form.html", {"form": form, "title": _("Edit User")})


@login_required
@role_required("admin")
def user_toggle_active(request, pk):
    if request.method != "POST":
        return redirect("core:user_list")
    pharmacy = getattr(request, "pharmacy", None)
    qs = User.objects.all()
    if pharmacy:
        qs = qs.filter(userprofile__pharmacy=pharmacy)
    user = get_object_or_404(qs, pk=pk)
    if user == request.user:
        messages.error(request, _("You cannot deactivate your own account."))
        return redirect("core:user_list")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    status = _("activated") if user.is_active else _("deactivated")
    messages.success(
        request, _("User %(name)s has been %(status)s.") % {"name": user.get_full_name(), "status": status}
    )
    return redirect("core:user_list")


@login_required
@role_required("admin")
def user_remove(request, pk):
    if request.method != "POST":
        return redirect("core:user_list")
    pharmacy = getattr(request, "pharmacy", None)
    qs = User.objects.all()
    if pharmacy:
        qs = qs.filter(userprofile__pharmacy=pharmacy)
    user = get_object_or_404(qs, pk=pk)
    if user == request.user:
        messages.error(request, _("You cannot remove your own account."))
        return redirect("core:user_list")
    user.is_active = False
    user.save(update_fields=["is_active"])
    try:
        profile = user.userprofile
        profile.pharmacy = None
        profile.save(update_fields=["pharmacy"])
    except UserProfile.DoesNotExist:
        pass
    messages.success(request, _("User %(name)s has been removed from the pharmacy.") % {"name": user.get_full_name()})
    return redirect("core:user_list")


@login_required
@role_required("admin")
def invitation_create(request):
    pharmacy = getattr(request, "pharmacy", None)
    invite_link = None
    if request.method == "POST":
        form = InvitationForm(request.POST, pharmacy=pharmacy)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.invited_by = request.user
            invitation.save()
            invite_link = request.build_absolute_uri(f"/invite/{invitation.token}/")
            # Send email
            try:
                html_message = render_to_string(
                    "emails/invitation.html",
                    {
                        "invitation": invitation,
                        "invite_link": invite_link,
                        "inviter": request.user,
                    },
                )
                send_mail(
                    subject=_("You've been invited to join %(pharmacy)s on Farmix") % {"pharmacy": pharmacy.name},
                    message=_("You've been invited to join %(pharmacy)s. Visit %(link)s to register.")
                    % {
                        "pharmacy": pharmacy.name,
                        "link": invite_link,
                    },
                    from_email=None,
                    recipient_list=[invitation.email],
                    html_message=html_message,
                )
                messages.success(request, _("Invitation sent to %(email)s.") % {"email": invitation.email})
            except Exception:
                messages.warning(request, _("Invitation created but email could not be sent. Share the link manually."))
            form = InvitationForm(pharmacy=pharmacy)
    else:
        form = InvitationForm(pharmacy=pharmacy)
    return render(
        request,
        "core/invitation_form.html",
        {
            "form": form,
            "invite_link": invite_link,
            "title": _("Invite User"),
        },
    )


@login_required
@role_required("admin")
def invitation_list(request):
    pharmacy = getattr(request, "pharmacy", None)
    invitations = Invitation.objects.filter(pharmacy=pharmacy).select_related("invited_by").order_by("-created_at")
    return render(
        request,
        "core/invitation_list.html",
        {
            "invitations": invitations,
            "title": _("Invitations"),
        },
    )


@login_required
@role_required("admin")
def invitation_revoke(request, pk):
    if request.method != "POST":
        return redirect("core:invitation_list")
    pharmacy = getattr(request, "pharmacy", None)
    invitation = get_object_or_404(Invitation, pk=pk, pharmacy=pharmacy)
    invitation.soft_delete(user=request.user)
    messages.success(request, _("Invitation to %(email)s has been revoked.") % {"email": invitation.email})
    return redirect("core:invitation_list")


@login_required
@role_required("admin")
def invitation_resend(request, pk):
    if request.method != "POST":
        return redirect("core:invitation_list")
    pharmacy = getattr(request, "pharmacy", None)
    invitation = get_object_or_404(Invitation, pk=pk, pharmacy=pharmacy)
    if invitation.is_accepted:
        messages.error(request, _("This invitation has already been accepted."))
        return redirect("core:invitation_list")
    # Reset expiry
    from datetime import timedelta
    from django.utils import timezone as tz

    invitation.expires_at = tz.now() + timedelta(days=7)
    invitation.save(update_fields=["expires_at", "updated_at"])
    invite_link = request.build_absolute_uri(f"/invite/{invitation.token}/")
    try:
        html_message = render_to_string(
            "emails/invitation.html",
            {
                "invitation": invitation,
                "invite_link": invite_link,
                "inviter": request.user,
            },
        )
        send_mail(
            subject=_("You've been invited to join %(pharmacy)s on Farmix") % {"pharmacy": pharmacy.name},
            message=_("You've been invited to join %(pharmacy)s. Visit %(link)s to register.")
            % {
                "pharmacy": pharmacy.name,
                "link": invite_link,
            },
            from_email=None,
            recipient_list=[invitation.email],
            html_message=html_message,
        )
        messages.success(request, _("Invitation resent to %(email)s.") % {"email": invitation.email})
    except Exception:
        messages.warning(request, _("Could not send email. Share the link manually: %(link)s") % {"link": invite_link})
    return redirect("core:invitation_list")


def invitation_accept(request, token):
    if request.user.is_authenticated:
        messages.info(request, _("You are already logged in. Log out first to accept an invitation."))
        return redirect("core:dashboard")
    invitation = get_object_or_404(Invitation, token=token)
    if invitation.is_accepted:
        messages.error(request, _("This invitation has already been accepted."))
        return redirect("login")
    if invitation.is_expired:
        messages.error(request, _("This invitation has expired. Please ask for a new one."))
        return redirect("login")
    if User.objects.filter(email__iexact=invitation.email).exists():
        messages.error(request, _("An account with this email already exists. Please log in."))
        return redirect("login")
    if request.method == "POST":
        form = InvitedUserRegistrationForm(request.POST, invitation=invitation)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="apps.core.backends.EmailBackend")
            messages.success(request, _("Welcome to %(pharmacy)s!") % {"pharmacy": invitation.pharmacy.name})
            return redirect("core:dashboard")
    else:
        form = InvitedUserRegistrationForm(invitation=invitation)
    return render(
        request,
        "registration/invitation_accept.html",
        {
            "form": form,
            "invitation": invitation,
            "title": _("Accept Invitation"),
        },
    )


@login_required
@role_required("admin")
def audit_log(request):
    logs = AuditLog.objects.select_related("user").order_by("-timestamp")
    pharmacy = getattr(request, "pharmacy", None)
    if pharmacy:
        logs = logs.filter(pharmacy=pharmacy)
    logs = logs[:200]
    return render(request, "core/audit_log.html", {"logs": logs, "title": _("Audit Log")})
