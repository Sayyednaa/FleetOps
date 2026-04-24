from core.models import Notification, MessageRecipient


def global_context(request):
    """Inject unread counts and user role into every template context."""
    if not request.user.is_authenticated:
        return {}
    return {
        'unread_notifications_count': Notification.objects.filter(
            user=request.user, is_read=False
        ).count(),
        'unread_messages_count': MessageRecipient.objects.filter(
            recipient=request.user, is_read=False
        ).count(),
        'user_role': request.user.role,
    }
