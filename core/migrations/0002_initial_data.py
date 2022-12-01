# Data Migration file for populating the initial database with REQUIRED data

from django.contrib.auth.hashers import make_password
from django.db import migrations


class Migration(migrations.Migration):

    # default groups
    def create_groups(apps, schema_editor):
        Group = apps.get_model('auth', 'Group')
        Group.objects.bulk_create([
            Group(name='educator'),
            Group(name='lab_assistant'),
            Group(name='student'),
        ])

    # default admin account
    def create_admin(apps, schema_editor):
        User = apps.get_model('core', 'User')
        User.objects.create(
            username="ADMIN",
            email='ADMIN@EXAMPLE.COM',
            password=make_password('password123'),
            is_staff=True,
            is_superuser=True,
        )

    # default languages and corresponding code templates
    def create_languages(apps, schema_editor):
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

    """
    The following functions are for demo purposes only.
    """

    def create_users(apps, schema_editor):
        Group = apps.get_model('auth', 'Group')
        User = apps.get_model('core', 'User')

        # educator 1
        User.objects.create(
            username="YRLOKE",
            first_name="YUAN REN",
            last_name="LOKE",
            email='YRLOKE@NTU.EDU.SG',
            password=make_password('password123'),
            is_staff=False,
            is_superuser=False,
        )
        # educator 2
        User.objects.create(
            username="LON898",
            first_name="LONG YAN",
            last_name="TAN",
            email='LON898@NTU.EDU.SG',
            password=make_password('password123'),
            is_staff=False,
            is_superuser=False,
        )
        # educator 3
        User.objects.create(
            username="TIM111",
            first_name="TIMOTHY",
            last_name="NG",
            email='TIM111@NTU.EDU.SG',
            password=make_password('password123'),
            is_staff=False,
            is_superuser=False,
        )
        # student
        User.objects.create(
            username="JLEE254",
            first_name="JUN WEI",
            last_name="LEE",
            email='JLEE254@E.NTU.EDU.SG',
            password=make_password('password123'),
            is_staff=False,
            is_superuser=False,
        )
        # lab assistant
        User.objects.create(
            username="LIM287",
            first_name="GRACE",
            last_name="LIM",
            email='LIM287@NTU.EDU.SG',
            password=make_password('password123'),
            is_staff=False,
            is_superuser=False,
        )
        Group.objects.get(name="educator").user_set.add(User.objects.get(username='YRLOKE'))
        Group.objects.get(name="educator").user_set.add(User.objects.get(username='LON898'))
        Group.objects.get(name="educator").user_set.add(User.objects.get(username='TIM111'))
        Group.objects.get(name="student").user_set.add(User.objects.get(username='JLEE254'))
        Group.objects.get(name="lab_assistant").user_set.add(User.objects.get(username='LIM287'))

    def create_question_banks(apps, schema_editor):
        User = apps.get_model('core', 'User')
        QuestionBank = apps.get_model('core', 'QuestionBank')

        # default admin question bank for testing
        QuestionBank.objects.create(
            name="Questions for Platform Familiarisation",
            description="Simple questions for familiarisation with the system.",
            owner=User.objects.get(username="LON898"),
            private=False
        )

        # Dr Loke's question bank
        QuestionBank.objects.create(
            name="Basic Algorithms Practice",
            description="These questions will be used to test the students on their understanding of basic algorithms.",
            owner=User.objects.get(username="YRLOKE"),
            private=True
        )

    def create_courses(apps, schema_editor):
        User = apps.get_model('core', 'User')
        Course = apps.get_model('core', 'Course')

        c = Course.objects.create(
            name="DATA STRUCTURES AND ALGORITHMS",
            code="SC1007",
            year=2022,
            owner=User.objects.get(username="YRLOKE"),
            semester='2',
        )

        # add maintainer
        c.maintainers.add(User.objects.get(username="LIM287"))

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups),
        migrations.RunPython(create_admin),
        migrations.RunPython(create_languages),
        migrations.RunPython(create_users),
        migrations.RunPython(create_question_banks),
        migrations.RunPython(create_courses),
    ]
