from django.contrib.auth import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import QuestionBank


@receiver(post_save, sender=QuestionBank)
def clear_shared_with(sender, instance, created, **kwargs):
    # if question bank is made public, clear the "shared_with" relationships
    if not instance.private:
        # mytodo: this M2M field is not cleared if updated via django admin!
        instance.shared_with.clear()


@receiver(user_logged_in)
def on_login(sender, user, request, **kwargs):
    """
    Calls set_session_key() to store the latest session key for a user and remove the previous session.
    """
    user.set_session_key(request.session.session_key)
