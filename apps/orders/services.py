from apps.core.models import AuditLog

from .models import Order, OrderStatusLog


class OrderWorkflowService:
    """Manages order status transitions with logging."""

    TRANSITION_MAP = {
        "send_for_quote": Order.send_for_quote,
        "quote_accepted": Order.quote_accepted,
        "recipe_received": Order.recipe_received,
        "start_production": Order.start_production,
        "production_complete": Order.production_complete,
        "mark_complete": Order.mark_complete,
        "cancel": Order.cancel,
        "mark_error": Order.mark_error,
    }

    @classmethod
    def transition(cls, order, action, user, comment=""):
        """Execute a named transition on an order with audit logging."""
        transition_method = cls.TRANSITION_MAP.get(action)
        if not transition_method:
            raise ValueError(f"Unknown transition: {action}")

        old_status = order.status
        transition_method(order)
        order.save()

        OrderStatusLog.objects.create(
            order=order,
            from_status=old_status,
            to_status=order.status,
            changed_by=user,
            comment=comment,
        )

        AuditLog.objects.create(
            pharmacy=order.pharmacy,
            user=user,
            action=AuditLog.Action.UPDATE,
            model_name="Order",
            object_id=str(order.pk),
            changes={"status": {"old": old_status, "new": order.status}, "comment": comment},
        )

        return order

    @classmethod
    def get_available_transitions(cls, order):
        """Return list of available transition names for an order."""
        available = []
        for name, method in cls.TRANSITION_MAP.items():
            # Check if transition is possible from current state
            transitions = order.get_available_status_transitions()
            target_states = [t.target for t in transitions]
            # Get the target of this named method
            field_transitions = getattr(method, "_django_fsm", None)
            if field_transitions:
                for ft in field_transitions.transitions.values():
                    if ft.target in target_states:
                        available.append(name)
                        break
        return available
