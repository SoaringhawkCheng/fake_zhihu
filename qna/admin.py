from flask_admin.contrib.sqla import ModelView

from . import db
from . import ad as admin
from .models import Question, Answer, User, Role


class QuestionView(ModelView):
    column_list = ('title', 'author', 'timestamp')
    column_labels = dict(title='标题', author='提问者', timestamp='提问时间')


class AnserView(ModelView):
    column_list = ('author', 'question', 'timestamp')
    column_labels = dict(author='回答者', question='回答的问题', timestamp='回答时间')


class UserView(ModelView):
    column_list = ('fullname', 'email', 'role')
    column_labels = dict(fullname='昵称', email='邮箱', role='用户角色')
    form_columns = ('fullname', 'email', 'role')


class RoleView(ModelView):
    column_list = ('name', 'permissions')
    column_labels = dict(name='角色各称', permissions='角色权限')


admin.add_view(QuestionView(Question, db.session))
admin.add_view(AnserView(Answer, db.session))
admin.add_view(UserView(User, db.session))
admin.add_view(RoleView(Role, db.session))
