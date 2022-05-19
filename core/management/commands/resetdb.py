import os
import shutil
from pathlib import Path

from django.core import management
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Resets the database (delete db -> delete migrations -> makemigrations --> default migration -> migrate)"

    def handle(self, *args, **options):
        self.stdout.write('Running reset database management command')

        # 'core' app directory
        core_app_path = Path(__file__).parents[2]

        # 'core/db.sqlite3'
        db_path = os.path.join(Path(__file__).parents[3], "db.sqlite3")

        # 'core/migrations' folder
        migrations_path = os.path.join(core_app_path, "migrations")

        # stage 1: delete database
        self.stdout.write('[1] Database:')

        # try to remove db
        try:
            os.remove(db_path)
            self.stdout.write('  - Deleted db.sqlite3!')
        except FileNotFoundError:
            self.stdout.write('  - Database not found, nothing to do here...')

        # stage 2: delete migrations
        self.stdout.write('[2] Delete migrations:')

        # find files in the migration folder
        migration_files = os.listdir(migrations_path)
        self.stdout.write(self.style.SUCCESS('  - Found these files: %s' % str(migration_files)))

        # remove migration files, except ignored files/directories
        ignored = ["__init__.py", "__pycache__", "default"]
        for file in migration_files:
            if file not in ignored:
                os.remove(os.path.join(migrations_path, file))
                self.stdout.write('  - Removed "%s"' % file)

        # stage 3: makemigrations
        self.stdout.write('[3] Calling makemigrations:')
        management.call_command('makemigrations')

        # stage 4: copy `default/default_migration.py` to `0002_initial.py`
        self.stdout.write('[4] Copying default migration file:')
        src = os.path.join(migrations_path, "default", "default_migration.py")
        dst = os.path.join(migrations_path, "0002_initial.py")
        try:
            shutil.copyfile(src, dst)
            self.stdout.write('  - Migration file \'0002_initial.py\' created!')
        except FileNotFoundError:
            self.stdout.write('  - \'_default_migration.py\' not found, nothing copied!')

        # stage 5: migrate
        self.stdout.write('[5] Calling migrate:')
        management.call_command('migrate')

        self.stdout.write(self.style.SUCCESS('\nSuccessfully completed resetdb!'))
