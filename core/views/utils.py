# utility functions for checking group membership
from core.models import CodeQuestionAttempt


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


# mytodo: refactor this to check_permissions_course()
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


def check_permissions_qb(question_bank, user):
    """
    Returns the permission level of a user for this question bank.
    0 - no permissions
    1 - owner shared with this user (viewing rights)
    2 - owner
    """
    if question_bank.owner == user:
        return 2
    if user in question_bank.shared_with.all():
        return 1
    return 0


def check_permissions_code_question(code_question, user):
    """
    Returns if a user can make changes to a code question.
    True - Has permission (is the owner of the question bank, or course containing the assessment)
    False - No permission
    2 - Read/Write
    1 - Read
    0 - No permissions
    """
    if code_question.question_bank:  # belongs to qb
        return check_permissions_qb(code_question.question_bank, user)
    else:  # belongs to assessment
        if check_permissions(code_question.assessment.course, user) != 0:
            return 2


def check_permissions_assessment(assessment, user):
    """
    Returns the permission level of a user for the course that this assessment belongs to.
    0 - no permissions
    1 - maintainer
    2 - owner
    """
    if assessment.course.owner == user:
        return 2
    if user in assessment.course.maintainers.all():
        return 1
    return 0


def get_assessment_attempt_question(assessment_attempt, question_index=None):
    """
    Get a specific question in an assessment attempt.
    If question_index is specified and within bounds, return only the question object.
    Else, return the entire list.
    """
    questions = []
    cq_attempts = list(CodeQuestionAttempt.objects.filter(assessment_attempt=assessment_attempt).order_by('id').prefetch_related('code_question'))
    statuses = [cqa.attempted for cqa in cq_attempts]

    if question_index is None:  # return all questions
        return statuses, cq_attempts
    elif question_index > len(cq_attempts) - 1:  # return None
        return [], None
    else:  # return specific question
        return statuses, cq_attempts[question_index]
