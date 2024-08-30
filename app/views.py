import pickle
from .modules import pinger
from app import app, forms, db, models, views_permission
from flask import render_template, request, redirect, url_for, flash, session, send_file, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from datetime import timedelta
from sqlalchemy import exc as db_exc
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from datetime import datetime
import logging
import os

app_logger = logging.getLogger('app')
admin_logger = logging.getLogger('admin_panel')


def generate_password_crypto(password):
    crypt = Fernet(key=app.config.get('DEIL_API_CRYPTO'))
    return crypt.encrypt(password.encode('utf-8'))


@app.route('/index', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
@login_required
def index():
    # app_logger.info(f'{current_user.login}: >> посетил главную страницу <<')
    user = db.session.query(models.User).get(current_user.id)
    user.last_visit = datetime.now()
    try:
        db.session.flush()
        db.session.commit()
    except Exception as e:
        app_logger.error('Ошибка при изменении даты посещения в базе данных')
        app_logger.exception(e)
    return render_template('main.html')


@app.route('/logout/', methods=['get'])
def logout():
    app_logger.info(f'{current_user.login}: >> вышел из аккаунта <<')
    logout_user()
    return redirect(url_for('login'))


@app.route('/login/', methods=['POST', 'GET'])
def login():
    session.pop('_flashes', None)  # очиска сообщений

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    login_form = forms.LoginForm()
    if request.method == 'POST':
        user = db.session.query(models.User).filter(models.User.login == login_form.username.data).first()
        if user and check_password_hash(user.passw, login_form.password.data):
            login_user(user, remember=True, duration=timedelta(days=30))
            app_logger.info(f'{current_user.login}: >> авторизовался на сервере <<')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль')

    return render_template('login.html', form=login_form)


@app.route('/admin_panel/', methods=['GET'])
@login_required
def admin_panel():
    return render_template('admin_panel/admin_panel.html')


@app.route('/admin_panel/users/', methods=['POST', 'GET'])
@login_required
def admin_users():
    user_lst = db.session.query(models.User).all()  # список users из БД
    return render_template('admin_panel/admin_user_list.html', users=user_lst)


@app.route('/admin_panel/add_user/', methods=['POST', 'GET'])
@login_required
@views_permission.admin_check
def add_user():
    session.pop('_flashes', None)  # очиска сообщений
    form = forms.CreateUserForm()  # форма ввода данных нового пользователя
    if request.method == 'POST' and form.is_submitted():
        try:
            db.session.add(
                models.User(
                    login=form.username.data,
                    passw=generate_password_hash(form.password.data),
                    privilege=form.privilege.data,
                    carbon_login=form.carbon_login.data,
                    carbon_passw=generate_password_crypto(form.carbon_passw.data),
                    user_data = '',
                    last_visit = None,
                )
            )
            db.session.commit()
            flash(
                message=f'Пользователь <{form.username.data}> успешно создан в БД',
                category='notify'
            )
            return redirect(url_for('admin_users'))
        except db_exc.IntegrityError:
            flash(
                message='Не удалось создать пользователя, возможно данный логин уже существует в БД',
                category='error'
            )
        except db_exc.SQLAlchemyError:
            flash(
                message='Не удалось создать пользователя, неивестная ошибка',
                category='error'
            )
    return render_template('admin_panel/admin_user_add.html', form=form)


@app.route('/admin_panel/del_user/', methods=['POST'])
@login_required
@views_permission.admin_check
def del_user():
    login = request.form.get('login')
    if login:
        try:
            db.session.delete(models.User.query.filter_by(login=login).first())
            db.session.commit()
            flash(
                message=f'Пользователь <{login}> успешно удалён',
                category=f'notify'
            )
        except db_exc.SQLAlchemyError:
            flash(
                message='Не удалось удалить пользователя',
                category='error'
            )
    else:
        flash(
            message='Неверные данные запроса',
            category='error'
        )
    return redirect(url_for('admin_users'))


@app.route('/admin_panel/change_user/', methods=['POST', 'GET'])
@login_required
@views_permission.admin_check
def change_user():
    def validate(data):
        if data and 3 <= len(data):
            return True
    user_login = request.args.get('login')
    form = forms.ChangeUserForm()

    if request.method == 'POST' and form.is_submitted():
        usr = models.User.query.filter_by(login=user_login).first()

        try:
            if validate(form.carbon_login.data):
                usr.carbon_login = form.carbon_login.data
            if validate(form.carbon_passw.data):
                usr.carbon_passw = generate_password_crypto(form.carbon_passw.data)
            if validate(form.username.data):
                usr.login = form.username.data
            if validate(form.password.data):
                usr.passw = generate_password_hash(form.password.data)
            if form.privilege.data == 'admin' or form.privilege.data == 'user':
                usr.privilege = form.privilege.data
            db.session.add(usr)
            db.session.commit()
        except db_exc.IntegrityError:
            flash(
                message=f'Данные не удалось изменить. Изменяемый логин уже существует',
                category='error'
            )
            return redirect(url_for('admin_users'))
        except db_exc.SQLAlchemyError:
            flash(
                message=f'Db Error. Неизвестная ошибка',
                category='error'
            )
            return redirect(url_for('admin_users'))
        flash(
            message=f'Данные пользователя <{form.username.data}> изменены',
            category='notify'
        )
        return redirect(url_for('admin_users'))
    form.username.data = user_login
    return render_template('admin_panel/admin_user_change.html', form=form)


@app.route('/admin_panel/icmp/', methods=['POST', 'GET'])
@login_required
@views_permission.admin_check
def admin_icmp():

    form = forms.ChangeIcmpParams()
    params = db.session.query(models.IcmpParams).get_or_404(1)
    if request.method == 'POST':
        params.ping_interval = form.ping_interval.data
        params.icmp_interval = form.icmp_interval.data
        params.icmp_count = form.icmp_count.data
        params.ping_workers = form.ping_workers.data
        params.icmp_timeout = form.icmp_timeout.data
        try:
            db.session.flush()
            db.session.commit()
            flash(
                message='Изменения применены',
                category='notify'
            )
        except db_exc.SQLAlchemyError:
            db.session.rollback()
            flash(
                message='Ошибка. Не удалость внести изменения в параметры ICMP',
                category='error'
            )
        # return render_template('admin_panel/admin_icmp_params.html', form=form)

    form.ping_interval.render_kw = {'min': 10, 'max': 600, 'value': params.ping_interval}
    form.icmp_interval.render_kw = {'min': 1, 'max': 10, 'value': params.icmp_interval}
    form.icmp_count.render_kw = {'min': 1, 'max': 10, 'value': params.icmp_count}
    form.ping_workers.render_kw = {'min': 5, 'max': 200, 'value': params.ping_workers}
    form.icmp_timeout.render_kw = {'min': 1, 'max': 10, 'value': params.icmp_timeout}

    return render_template('admin_panel/admin_icmp_params.html', form=form)


@app.route('/admin_panel/logs/', methods=['POST', 'GET'])
@login_required
def admin_logs():
    with open(file='./file.log', encoding='utf-8') as log:
        return render_template('admin_panel/admin_logs.html', logs=log.read())


@app.route('/admin_panel/logs/clear', methods=['POST', 'GET'])
@login_required
@views_permission.admin_check
def admin_clear_logs():
    with open(file='./file.log', encoding='utf-8', mode='w') as log:
        log.write('')
        admin_logger.info(f'Пользователь <{current_user.login}> очистил логи')
        return redirect(url_for('admin_logs'))






