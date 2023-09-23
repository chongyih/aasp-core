# Generated by Django 4.0.3 on 2023-09-23 09:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_hdl_language_indication'),
    ]

    operations = [
        migrations.CreateModel(
            name='HDLQuestionSolution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module', models.TextField(blank=True, null=True)),
                ('testbench', models.TextField(blank=True, null=True)),
                ('code_question', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.codequestion')),
            ],
        ),
        migrations.CreateModel(
            name='HDLQuestionConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_type', models.IntegerField(choices=[(1, 'Module Design'), (2, 'Testbench Design'), (3, 'Module and Testbench Design')], default=1)),
                ('question_config', models.IntegerField(choices=[(1, 'Generate module code')], default=1)),
                ('code_question', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.codequestion')),
            ],
        ),
    ]