# Default migration, do not delete

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

    def create_users(apps, schema_editor):
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

    def create_courses(apps, schema_editor):
        User = apps.get_model('core', 'User')
        Course = apps.get_model('core', 'Course')

        c = Course.objects.create(
            name="SOFTWARE SECURITY",
            code="CZ4067",
            year=2022,
            owner=User.objects.get(username="YRLOKE"),
            semester='2',
        )

        # add maintainer
        c.maintainers.add(User.objects.get(username="LIM287"))
        c.maintainers.add(User.objects.get(username="ADMIN"))

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_groups),
        migrations.RunPython(create_admin),
        migrations.RunPython(create_users),
        migrations.RunPython(create_courses),
    ]
