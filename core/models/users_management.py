from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models


class User(AbstractUser):
    # override email field to make it unique and required
    email = models.EmailField(null=False, blank=False, unique=True)

    # override name fields to make them required
    first_name = models.CharField("first name", max_length=150, blank=False)
    last_name = models.CharField("last name", max_length=150, blank=False)

    class Meta:
        permissions = (
            ("can_create_student", "Can create student accounts"),
            ("can_create_educator", "Can create educator accounts"),
            ("can_create_lab_assistant", "Can create lab assistant accounts")
        )

    def clean(self):
        super().clean()

        # capitalize these fields
        self.first_name = self.first_name.upper()
        self.last_name = self.last_name.upper()
        self.email = self.email.upper()
        self.username = self.username.upper()

    @property
    def name(self):
        return f"{self.last_name} {self.first_name}"


class Course(models.Model):
    class Semesters(models.TextChoices):
        SEMESTER_1 = ('1', "SEMESTER 1")
        SEMESTER_2 = ('2', "SEMESTER 2")
        SPECIAL_TERM = ('0', "SPECIAL TERM")

    class Meta:
        permissions = (
            ("can_add_students", "Can add students to the course"),
            ("can_remove_students", "Can remove students from the course"),
        )

    name = models.CharField(max_length=150, blank=False, null=False)
    code = models.CharField(max_length=20, blank=False, null=False)
    students = models.ManyToManyField(User, related_name='registered_courses', blank=True)
    year = models.PositiveSmallIntegerField(validators=[MaxValueValidator(9999)], blank=False, null=False)  # e.g. 2017 (means AY17/18)
    semester = models.CharField(max_length=1, choices=Semesters.choices, default=Semesters.SEMESTER_1, blank=False, null=False)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    maintainers = models.ManyToManyField(User, related_name='maintained_courses', blank=True)  # maintainers can modify, but not delete the course

    def __str__(self):
        return f"{self.code} {self.name} (AY{str(self.year)[2:]}/{str(self.year+1)[2:]} S{self.semester})"

    @property
    def short_name(self):
        return f"{self.code} (AY{str(self.year)[2:]}/{str(self.year+1)[2:]} S{self.semester})"

    def clean(self):
        super().clean()

        # capitalize these fields
        self.name = self.name.upper()
        self.code = self.code.upper()

    def get_permissions(self, user):
        """
        Returns the permission level of a user for this course.
        0 - no permissions
        1 - maintainer
        2 - owner
        """
        if self.owner == user:
            return 2
        if user in self.maintainers.all():
            return 1
        return 0
