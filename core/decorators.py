from enum import Enum

from django.core.exceptions import PermissionDenied


class UserGroup(Enum):
    educator = "Educator"
    student = "Student"
    lab_assistant = "Lab Assistant"


def groups_allowed(*groups: UserGroup):
    def decorator(function):
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(
                    name__in=[group.name for group in groups]
            ).exists():
                return function(request, *args, **kwargs)
            raise PermissionDenied()

        return wrapper

    return decorator
