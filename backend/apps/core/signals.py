from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import User, Notification


@receiver(pre_save, sender=User)
def update_user_timestamp(sender, instance, **kwargs):
    """
    Update the updated_at field.
    """
    instance.updated_at = timezone.now()


@receiver(post_save, sender=User)
def create_welcome_notification(sender, instance, created, **kwargs):
    """
    Create a welcome notification when a new user is created.
    """
    if created:
        Notification.objects.create(
            user=instance,
            title="Welcome to SebaCox",
            message="Welcome to SebaCox! Your account has been created successfully.",
            notification_type="system"
        )
