#!/usr/bin/env python
import os
from datetime import datetime

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell
from subprocess import call

from qna import create_app, db
from qna.models import User, Role, Permission, Question

app = create_app(os.getenv('APP_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role,
                Permission=Permission, Question=Question)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

basedir = os.path.abspath(os.path.dirname(__file__))


@manager.command
def migrate():
    if not os.path.exists(os.path.join(basedir, 'migrations')):
        call('python manage.py db init')
    call('python manage.py db migrate -m "%s"' %
         datetime.now().strftime('%Y%m%d_%H%M'))
    call('python manage.py db upgrade')
    roles = Role.query.all()
    if not roles:
        Role.insert_roles()


@manager.command
def removedata():
    import os
    import shutil
    from glob import glob
    fname_list = glob('*.sqlite')
    for fname in fname_list:
        os.remove(fname)
    if not os.path.exists(os.path.join(basedir, 'migrations')):
        raise Exception('migrations is not exists.')
    else:
        shutil.rmtree(os.path.join(basedir, 'migrations'))


@manager.command
def createsuperuser():
    import getpass
    username = input('Username: ')
    email = input('Email address: ')
    password = getpass.getpass(prompt='Password: ')
    password_again = getpass.getpass(prompt='Password (again): ')


@manager.command
def deploy():
    from flask_migrate import upgrade
    from qna.models import Role

    upgrade()
    Role.insert_roles()


if __name__ == '__main__':
    manager.run()
