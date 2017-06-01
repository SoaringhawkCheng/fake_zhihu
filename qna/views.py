from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import current_user, login_required, login_user, logout_user

from . import db
from .models import Question, Answer, User

site = Blueprint('site', __name__)


@site.route('/', methods=['GET', 'POST'])
def home():
    # if not current_user.is_authenticated:
    #     return render_template('auth/signup.html')
    questions = Question.query.all()
    return render_template('home.html', questions=questions)


@site.route('/explore')
def explore():
    return render_template('explore.html')


@site.route('/ask', methods=['GET', 'POST'])
@login_required
def ask_question():
    if current_user.is_authenticated and request.method == 'POST':
        question = Question(title=request.form.get("title"),
                            description=request.form.get("content"),
                            author=current_user._get_current_object())
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('.question', id=question.id))
    elif not current_user.is_authenticated:
        return redirect(url_for('site.signin'))


@site.route('/question/<int:id>', methods=['GET', 'POST'])
def question(id):
    question = Question.query.get_or_404(id)
    if request.method == 'POST':
        answer = Answer(content=request.form['answer'],
                        question=question,
                        author=current_user._get_current_object())
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('.question', id=question.id))
    answers = question.answers.order_by(Answer.timestamp.asc()).all()
    return render_template('question.html', question=question, answers=answers)


@site.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        key_word = request.form.get('q')
        print(key_word)
        results = Question.query.whoosh_search(key_word)
        return render_template('search.html', key_word=key_word,
                               results=results)


@site.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        return redirect(url_for('site.home'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('account')).first()
        if user is not None and user.verify_password(request.form.get('password')):
            login_user(user, remember=True)
            return redirect(request.args.get('next') or url_for('site.home'))
    return render_template('auth/signin.html')


@site.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('site.home'))


@site.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = User(email=request.form.get("email"),
                    fullname=request.form.get("fullname"),
                    password=request.form.get("password"))
        print(user.email, user.fullname, request.form.get("password"))
        print(request.form.get("email"))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('site.signin'))
    return render_template('auth/signup.html')


@site.app_errorhandler(404)
def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404
