from django.core.mail import send_mail
from django.utils import timezone
from .models import Notification, User
import logging

logger = logging.getLogger(__name__)


def send_notification(user, title, message, notification_type, content_type=None, object_id=None):
    """
    Send a notification to a user.
    """
    try:
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            content_type=content_type,
            object_id=object_id
        )
        # TODO: Send push notification to device tokens
        return notification
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return None


def send_email_notification(user_email, subject, message):
    """
    Send email notification.
    """
    try:
        send_mail(
            subject,
            message,
            'noreply@sebacox.com',
            [user_email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Error sending email: {e}")


def mark_notification_as_read(notification_id):
    """
    Mark a notification as read.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return notification
    except Notification.DoesNotExist:
        return None
