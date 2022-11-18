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

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups),
        migrations.RunPython(create_admin),
        migrations.RunPython(create_languages),
    ]
