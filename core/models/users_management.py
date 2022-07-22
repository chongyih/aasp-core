from django.contrib.auth.models import AbstractUser
from django.contrib.sessions.models import Session
from django.core.validators import MaxValueValidator
from django.db import models


class User(AbstractUser):
    # override email field to make it unique and required
    email = models.EmailField(null=False, blank=False, unique=True)

    # override name fields to make them required
    first_name = models.CharField("first name", max_length=150, blank=False)
    last_name = models.CharField("last name", max_length=150, blank=False)

    # add session field (used for enforcing single session)
    session_key = models.CharField(max_length=32, null=True, blank=True)

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

    def set_session_key(self, new_key):
        # remove previous session key from the database
        if self.session_key and not self.session_key == new_key:
            try:
                Session.objects.get(session_key=self.session_key).delete()
            except Session.DoesNotExist:
                print("Old session key does not exist in Session table. Deletion skipped.")

        # store the new session key
        self.session_key = new_key
        self.save()


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
    year = models.PositiveIntegerField(validators=[MaxValueValidator(9999)], blank=False, null=False)  # e.g. 2017 (means AY17/18)
    semester = models.CharField(max_length=1, choices=Semesters.choices, default=Semesters.SEMESTER_1, blank=False, null=False)
    owner = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    maintainers = models.ManyToManyField(User, related_name='maintained_courses', blank=True)  # maintainers can modify, but not delete the course
    active = models.BooleanField(default=True, blank=False, null=False)

    def __str__(self):
        return f"{self.code} {self.name} (AY{str(self.year)[2:]}/{str(self.year+1)[2:]} {self.get_semester_display()})"

    @property
    def short_name(self):
        return f"{self.code} (AY{str(self.year)[2:]}/{str(self.year+1)[2:]} S{self.get_semester_display()})"

    def clean(self):
        super().clean()

        # capitalize these fields
        self.name = self.name.upper()
        self.code = self.code.upper()

    def students_count(self):
        return User.objects.filter(enrolled_groups__course=self).count()


class CourseGroup(models.Model):
    name = models.CharField(max_length=20, blank=False, null=False)
    course = models.ForeignKey(Course, blank=False, null=False, on_delete=models.RESTRICT)
    students = models.ManyToManyField(User, related_name='enrolled_groups', blank=True)

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        super().clean()
        self.name = self.name.upper()

    def students_enrolled(self):
        return self.students.count()
