from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import LandParcel, Device

@receiver(post_save, sender=LandParcel)
def update_field_count_on_save(sender, instance, created, **kwargs):
    if created:
        instance.user.field_count += 1
        instance.user.save()

@receiver(post_delete, sender=LandParcel)
def update_field_count_on_delete(sender, instance, **kwargs):
    instance.user.field_count -= 1
    instance.user.save()


@receiver(post_save, sender=Device)
def update_device_count_on_save(sender, instance, created, **kwargs):
    if created:
        instance.user.device_count += 1
        instance.user.save()


@receiver(post_delete, sender=Device)
def update_device_count_on_delete(sender, instance, **kwargs):
    instance.user.device_count -= 1
    instance.user.save()