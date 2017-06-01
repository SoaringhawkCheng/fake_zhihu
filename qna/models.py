from datetime import datetime

from bs4 import BeautifulSoup
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from jieba.analyse import ChineseAnalyzer
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash

from . import db, login_manager


class Permission:
    """FOLLOW：表示是否能够关注其它用户的权限
    COMMENT：表示是否能够发表评论的权限
    WRITE_ARTICLES：表示是否能够写文章的权限
    MODERATE_COMMENTS：表示是否能够管理评论的权限
    ADMINISTER：表示是否能够管理网站的权限"""
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
        }

        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

    def __str__(self):
        return '%s' % self.name


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    questions = db.relationship('Question', backref='author', lazy='dynamic')
    answers = db.relationship('Answer', backref='author', lazy='dynamic')
    question_comments = db.relationship('QuestionComment', backref='author',
                                        lazy='dynamic')
    answer_comments = db.relationship('AnswerComment', backref='author',
                                      lazy='dynamic')
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN_EMAIL']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=False).first()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    # 设置密码散列值
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 使用密码和密码散列值进行验证
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can(self, permissions):
        return self.role is not None and \
               (self.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(followed=user)
            self.followed.append(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            self.followed.remove(f)

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    def __str__(self):
        return '%s' % self.fullname

    def __repr__(self):
        return '<User %r>' % self.fullname


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


topic_question_table = db.Table('topic_question_table',
                                db.Column('topic_id',
                                          db.Integer,
                                          db.ForeignKey('topics.id')),
                                db.Column('question_id',
                                          db.Integer,
                                          db.ForeignKey('questions.id')))


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    description = db.Column(db.Text)
    questions = db.relationship('Question', secondary=topic_question_table,
                                backref=db.backref('topics', lazy='dynamic'),
                                lazy='dynamic')

    def __repr__(self):
        return '<Topic %r>' % self.name

    def __str__(self):
        return '%s' % self.name


class Question(db.Model):
    __tablename__ = 'questions'
    __searchable__ = ['title', 'description']
    __analyzer__ = ChineseAnalyzer()
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    description = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    comments = db.relationship('QuestionComment', backref='question',
                               lazy='dynamic')
    answers = db.relationship('Answer', backref='question', lazy='dynamic')

    def __repr__(self):
        return '<Question %r>' % self.title

    def __str__(self):
        return '%s' % self.title


class Comment():
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)


class QuestionComment(Comment, db.Model):
    __tablename__ = 'question_comments'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    summary = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('AnswerComment', backref='answer',
                               lazy='dynamic')
    summary_img_url = db.Column(db.Text)

    @staticmethod
    def content_changed(target, value, oldvalue, initiator):
        extensions = ['markdown.extensions.extra',
                      'markdown.extensions.fenced_code',
                      'markdown.extensions.footnotes',
                      'markdown.extensions.tables',
                      'markdown.extensions.codehilite',
                      'markdown.extensions.wikilinks',
                      ]
        target.content_html = markdown(value,
                                       extensions=extensions,
                                       output_format='html')
        lines = value.split('\n')
        summary_text = '\n'.join(lines[:5])
        target.summary = markdown(summary_text,
                                  extensions=extensions,
                                  output_format='html')
        soup = BeautifulSoup(target.content_html, 'html.parser')
        if soup.find('img') is not None:
            target.summary_img_url = soup.find('img')['src']


db.event.listen(Answer.content, 'set', Answer.content_changed)


class AnswerComment(Comment, db.Model):
    __tablename__ = 'answer_comments'
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
