def global_context(request):
    """Add global context variables available to all templates."""
    context = {
        "app_name": "Farmix",
    }
    pharmacy = getattr(request, "pharmacy", None)
    if pharmacy:
        context["pharmacy_name"] = pharmacy.name
        context["pharmacy_anf_number"] = pharmacy.anf_number
        context["pharmacy_nif"] = pharmacy.nif
        context["pharmacy_address"] = pharmacy.address
        context["pharmacy_phone"] = pharmacy.phone
        context["pharmacy_technical_director"] = pharmacy.technical_director
    else:
        context["pharmacy_name"] = ""
        context["pharmacy_anf_number"] = ""
        context["pharmacy_nif"] = ""
        context["pharmacy_address"] = ""
        context["pharmacy_phone"] = ""
        context["pharmacy_technical_director"] = ""

    if request.user.is_authenticated:
        try:
            context["user_role"] = request.user.userprofile.role
            context["user_profile"] = request.user.userprofile
        except AttributeError:
            pass
    return context
