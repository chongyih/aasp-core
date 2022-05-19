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
    - duplicated rows
    - rows with duplicated values in matriculation number, email or username
    """
    # stores all removed rows by this cleaning function
    removed = []

    # remove duplicated rows by converting to set
    rows = set(rows)

    # split rows into fields and remove rows that do not have exactly 5 fields
    cleaned = []
    for row in rows:
        fields = row.split(",")
        if len(fields) != 5:
            removed.append(fields)
        else:
            cleaned.append(fields)

    # find duplicated values in matriculation number, email or username (e.g. two different rows with same matriculation_number, etc)
    seen_identification = set()
    duplicates_identification = [x[2] for x in cleaned if x[2] in seen_identification or seen_identification.add(x[2])]
    seen_email = set()
    duplicates_email = [x[3] for x in cleaned if x[3] in seen_email or seen_email.add(x[3])]
    seen_username = set()
    duplicates_username = [x[4] for x in cleaned if x[4] in seen_username or seen_username.add(x[4])]

    # remove rows with duplicated values in matriculation number, email or username
    cleaned2 = []
    for row in cleaned:
        if row[2] in duplicates_identification or row[3] in duplicates_email or row[4] in duplicates_username:
            removed.append(row)
        else:
            cleaned2.append(row)

    return cleaned2, removed
