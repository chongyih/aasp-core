from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import QuestionBank


@receiver(post_save, sender=QuestionBank)
def clear_shared_with(sender, instance, created, **kwargs):
    print("signal triggered")
    if not instance.private:
        instance.shared_with.clear()
