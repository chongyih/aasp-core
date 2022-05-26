# utility functions for checking group membership
def is_student(user):
    return user.is_superuser or user.groups.filter(name='student').exists()


def is_educator(user):
    return user.is_superuser or user.groups.filter(name='educator').exists()


def is_lab_assistant(user):
    return user.is_superuser or user.groups.filter(name='lab_assistant').exists()


def clean_csv(rows):
    """
    Removes:
    - header row, if it exists
    - duplicated rows
    - rows with duplicated values in username (but different names, group, etc)
    """
    # stores all removed rows by this cleaning function
    removed = []

    # remove header row if it exists
    if "FIRST_NAME,LAST_NAME,USERNAME,GROUP" in rows[0]:
        del rows[0]

    # remove duplicated rows by converting to set
    rows = set(rows)

    # split rows into fields and remove rows that do not have exactly 4 fields
    cleaned = []
    for row in rows:
        fields = row.split(",")
        if len(fields) != 4:
            removed.append(fields)
        else:
            cleaned.append(fields)

    # find duplicated values in username (e.g. two different rows with same username, etc)
    seen_username = set()
    duplicates_username = [x[2] for x in cleaned if x[2] in seen_username or seen_username.add(x[2])]

    # remove rows with duplicated values in username
    cleaned2 = []
    for row in cleaned:
        if row[2] in duplicates_username:
            removed.append(row)
        else:
            cleaned2.append(row)

    return cleaned2, removed


def check_permissions(course, user):
    """
    Returns the permission level of a user for this course.
    0 - no permissions
    1 - maintainer
    2 - owner
    """
    if course.owner == user:
        return 2
    if user in course.maintainers.all():
        return 1
    return 0
