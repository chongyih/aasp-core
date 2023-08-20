from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.core import management
from django.core.management import BaseCommand


def create_groups():
    Group = apps.get_model('auth', 'Group')
    Group.objects.bulk_create([
        Group(name='educator'),
        Group(name='lab_assistant'),
        Group(name='student'),
    ])


def create_admin():
    User = apps.get_model('core', 'User')
    User.objects.create(
        username="ADMIN",
        email='ADMIN@EXAMPLE.COM',
        password=make_password('password123'),
        is_staff=True,
        is_superuser=True,
    )


def create_users():
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('core', 'User')

    User.objects.create(
        username="YRLOKE",
        first_name="YUAN REN",
        last_name="LOKE",
        email='YRLOKE@NTU.EDU.SG',
        password=make_password('password123'),
        is_staff=False,
        is_superuser=False,
    )
    User.objects.create(
        username="JLEE254",
        first_name="JUN WEI",
        last_name="LEE",
        email='JLEE254@E.NTU.EDU.SG',
        password=make_password('password123'),
        is_staff=False,
        is_superuser=False,
    )
    User.objects.create(
        username="LIM287",
        first_name="JASMINE",
        last_name="LIM",
        email='LIM287@NTU.EDU.SG',
        password=make_password('password123'),
        is_staff=False,
        is_superuser=False,
    )
    Group.objects.get(name="educator").user_set.add(User.objects.get(username='YRLOKE'))
    Group.objects.get(name="student").user_set.add(User.objects.get(username='JLEE254'))
    Group.objects.get(name="lab_assistant").user_set.add(User.objects.get(username='LIM287'))


def create_courses():
    User = apps.get_model('core', 'User')
    Course = apps.get_model('core', 'Course')

    c = Course.objects.create(
        name="SOFTWARE SECURITY",
        code="CZ4067",
        year=2022,
        owner=User.objects.get(username="ADMIN"),
        semester='2',
    )

    # add maintainer
    c.maintainers.add(User.objects.get(username="LIM287"))
    c.maintainers.add(User.objects.get(username="YRLOKE"))


def create_tags():
    Tag = apps.get_model('core', 'Tag')
    Tag.objects.bulk_create([
        Tag(name='Easy'),
        Tag(name='Medium'),
        Tag(name='Hard'),
        Tag(name='Arrays'),
        Tag(name='Stack'),
        Tag(name='Linked List'),
    ])


def create_languages():
    Language = apps.get_model('core', 'Language')
    CodeTemplate = apps.get_model('core', 'CodeTemplate')

    c = Language.objects.create(name='C (GCC 9.2.0)', judge_language_id=50, ace_mode='c_cpp')
    java = Language.objects.create(name='Java (OpenJDK 13.0.1)', judge_language_id=62, ace_mode='java')
    python3 = Language.objects.create(name='Python 3.8.1', judge_language_id=71, ace_mode='python')

    # create code templates
    ct1 = CodeTemplate(language=c, name="Default",
                       code="// ro-start\n#include <stdio.h>\n#include <stdlib.h>\n\nint main(){\n// ro-end\n	// enter your solution here...\n\n\n// ro-start\n	return 0;\n}\n// ro-end\n")
    ct2 = CodeTemplate(language=java, name="Default",
                       code="// ro-start\npublic class Main {\n    public static void main(String [] args) {\n// ro-end\n        // enter your solution here...\n\n// ro-start\n    }\n}\n// ro-end\n")
    ct3 = CodeTemplate(language=python3, name="Default",
                       code='# // ro-start\ndef main():\n# // ro-end\n	# enter your solution here...\n\n\n# // ro-start\nif __name__ == "__main__":\n	main()\n# // ro-end\n')

    CodeTemplate.objects.bulk_create([ct1, ct2, ct3])


def create_question_bank():
    User = apps.get_model('core', 'User')
    QuestionBank = apps.get_model('core', 'QuestionBank')

    qb = QuestionBank.objects.create(
        name="Basic Algorithms Practice",
        description="These questions will be used to test the students on their understanding of basic algorithms.",
        owner=User.objects.get(username="ADMIN"),
        private=True
    )


def create_code_question():
    Tag = apps.get_model('core', 'Tag')
    QuestionBank = apps.get_model('core', 'QuestionBank')
    Language = apps.get_model('core', 'Language')
    CodeQuestion = apps.get_model('core', 'CodeQuestion')
    TestCase = apps.get_model('core', 'TestCase')
    CodeSnippet = apps.get_model('core', 'CodeSnippet')

    cq = CodeQuestion.objects.create(
        name="Two Sum",
        description="Given an array of integers `nums` and an integer target, "
                    "return indices of the two numbers such that they add up to `target`.",
        question_bank=QuestionBank.objects.get(id=1),
    )

    TestCase.objects.create(
        code_question=cq,
        stdin='sample in',
        stdout='sample out',
        time_limit=10,
        memory_limit=40960,
        score=0,
        hidden=False,
        sample=True,
    )

    TestCase.objects.create(
        code_question=cq,
        stdin='in1',
        stdout='out1',
        time_limit=10,
        memory_limit=40960,
        score=5,
        hidden=False,
    )

    TestCase.objects.create(
        code_question=cq,
        stdin='in2',
        stdout='out2',
        time_limit=10,
        memory_limit=40960,
        score=5
    )

    CodeSnippet.objects.create(
        code_question=cq,
        language=Language.objects.get(id=3),
        code="""# // ro-start
def main():
# // ro-end
    # enter your solution here


# // ro-start
main()
# // ro-end""")

    cq.tags.add(Tag.objects.get(id=1))
    cq.tags.add(Tag.objects.get(id=4))


class Command(BaseCommand):
    help = "Generate a fresh database and populate with required initial data. (makemigration -> migrate -> populate)"

    def handle(self, *args, **kwargs):
        self.stdout.write('[1] Calling makemigration:')
        management.call_command('makemigrations')

        self.stdout.write('[2] Calling migrate:')
        management.call_command('migrate')

        self.stdout.write('[3] Populating database:')

        # populate
        create_groups()
        create_admin()
        create_users()
        create_courses()
        create_tags()
        create_languages()
        create_question_bank()
        create_code_question()

        self.stdout.write(self.style.SUCCESS('\nSuccessfully completed gendb!'))
