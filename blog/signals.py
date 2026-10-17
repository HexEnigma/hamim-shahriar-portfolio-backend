from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Comment, Post


@receiver(post_save, sender=Comment)
def notify_owner_of_comment(sender, instance, created, **kwargs):
    if created and not instance.is_approved:
        send_mail(
            subject=f"New comment awaiting approval on “{instance.post.title}”",
            message=f"{instance.name} wrote:\n\n{instance.content}\n\nModerate it in your dashboard.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.OWNER_NOTIFY_EMAIL],
            fail_silently=True,
        )


@receiver(post_delete, sender=Post)
def delete_cover_file(sender, instance, **kwargs):
    if instance.cover_image:
        instance.cover_image.delete(save=False)