from django.contrib.auth.models import Group
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Review

User = settings.AUTH_USER_MODEL  # Or import your User directly

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def assign_user_group(sender, instance, created, **kwargs):
    if created:
        # Ensure the group exists (created in migration)
        group_name = instance.role.capitalize()  # 'customer' → 'Customer'
        try:
            group = Group.objects.get(name=group_name)
            instance.groups.add(group)
        except Group.DoesNotExist:
            # Optionally log or raise warning
            print(f"Group '{group_name}' does not exist. Please run migrations.")

@receiver([post_save, post_delete], sender=Review)
def update_product_rating(sender, instance, **kwargs):
    instance.product.update_average_rating()
