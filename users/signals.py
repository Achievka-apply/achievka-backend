from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile_exists(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
