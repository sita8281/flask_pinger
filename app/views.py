import pickle
from .modules import pinger, nas_poller, vpn_gateway
from app import app, forms, db, models, views_permission
from .deil_api_context import DeilContext
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


@app.route('/admin_panel/gpon/', methods=['POST', 'GET'])
@login_required
def admin_gpon():
    params_list = db.session.query(models.GponParams).all()
    forms_list = []
    for params in params_list:
        form = forms.ChangeGponParams()
        form.name.data = params.name
        form.tag.data = params.tag
        form.ip.data = params.ip
        form.port.data = params.port
        form.login.data = params.login
        form.passw.data = params.passw

        forms_list.append((params.id, form))

    return render_template('admin_panel/admin_gpon_params.html', forms=forms_list)


@app.route('/admin_panel/gpon/params/<iid>', methods=['POST'])
@login_required
@views_permission.admin_check
def admin_gpon_params(iid):
    params_row = db.session.query(models.GponParams).get_or_404(int(iid))
    form = forms.ChangeGponParams()
    try:
        params_row.name = form.name.data
        params_row.tag = form.tag.data
        params_row.ip = form.ip.data
        params_row.port = form.port.data
        params_row.login = form.login.data
        params_row.passw = form.passw.data

        db.session.flush()
        db.session.commit()

        flash(
            message="Изменения применены",
            category="notify"
        )

    except db_exc.SQLAlchemyError:

        db.session.rollback()

        flash(
            message="Ошибка БД. Не удалось применить изменения",
            category="error"
        )
    return redirect(url_for('admin_gpon'))


@app.route('/admin_panel/gpon/profiles/', methods=['POST', 'GET'])
@login_required
def admin_gpon_pfl():
    pfls = db.session.query(models.GponProfiles).all()
    form = forms.CreateGponProfile()
    return render_template('admin_panel/admin_gpon_profiles.html', profiles=pfls, form=form)


@app.route('/admin_panel/gpon/add_profile/', methods=['POST', 'GET'])
@login_required
@views_permission.admin_check
def admin_gpon_add():

    form = forms.CreateGponProfile()

    try:
        db.session.add(
            models.GponProfiles(
                name=form.name.data,
                vlan=form.vlan.data,
                gemport=form.gemport.data,
                srv_profile=form.srv_profile.data,
                line_profile=form.line_profile.data
            )
        )
        db.session.flush()
        db.session.commit()
        flash(
            message=f'Профиль <{form.name.data}> успешно создан в БД',
            category='notify'
        )
    except db_exc.IntegrityError:
        db.session.rollback()
        flash(
            message='Не удалось создать профиль, возможно данный профиль уже существует в БД',
            category='error'
        )
    except db_exc.SQLAlchemyError:
        db.session.rollback()
        flash(
            message='Ошибка БД. Не удалось создать профиль, неивестная ошибка',
            category='error'
        )

    return redirect(url_for('admin_gpon_pfl'))


@app.route('/admin_panel/gpon/delete_profile/<iid>', methods=['POST', 'GET'])
@login_required
@views_permission.admin_check
def admin_gpon_del(iid):
    pfl = db.session.query(models.GponProfiles).get_or_404(int(iid))
    try:
        db.session.delete(pfl)
        db.session.commit()
        flash(
            message="Профиль успешно удалён",
            category="notify"
        )

    except db_exc.SQLAlchemyError:
        flash(
            message="Ошибка БД. Не удалось удалить профиль",
            category="error"
        )
    return redirect(url_for('admin_gpon_pfl'))


@app.route('/admin_panel/carbon/', methods=['POST', 'GET'])
@login_required
def admin_carbon():
    form = forms.ChangeCarbonApi()
    params_api = db.session.query(models.CarbonApiParams).get_or_404(1)
    last_update = db.session.query(models.CarbonApiData).get_or_404(1).date
    if request.method == 'POST':
        params_api.name = form.name.data
        params_api.ip = form.ip.data
        params_api.port = form.port.data

        try:
            db.session.flush()
            db.session.commit()
            flash(message='Изменения применены', category='notify')
        except db_exc.SQLAlchemyError:
            db.session.rollback()
            flash(message='Ошибка БД. Не удалось применить изменения', category='error')

        return redirect(url_for('admin_carbon'))

    form.name.data = params_api.name
    form.ip.data = params_api.ip
    form.port.data = params_api.port
    return render_template('admin_panel/admin_carbon_params.html', form=form, last_update=last_update)


@app.route('/admin_panel/carbon/dump/', methods=['POST', 'GET'])
@login_required
def admin_carbon_dump():
    with DeilContext() as deil_api:
        tree = deil_api.get_tree_users()
    users_data = db.session.query(models.CarbonApiData).get_or_404(1)
    users_data.date = datetime.now().strftime('%Y/%m/%d %H:%M')
    users_data.data = pickle.dumps(tree)

    try:
        db.session.flush()
        db.session.commit()
        flash(message='Список пользователей Carbon обновлён', category='notify')
    except db_exc.SQLAlchemyError:
        db.session.rollback()
        flash(message='Ошибка БД. Не удалось записать обновлённый список', category='error')

    return redirect(url_for('admin_carbon'))


@app.route('/admin_panel/state/', methods=['POST', 'GET'])
@login_required
def admin_state():
    threads_states = {
        'nas_daemon': nas_poller.is_alive(),
        'icmp_daemon': pinger.is_alive(),
        'vpn_daemon': vpn_gateway.is_alive()
    }
    return render_template('admin_panel/admin_state.html', states=threads_states)


@app.route('/admin_panel/nas_params/', methods=['POST', 'GET'])
@login_required
def admin_nas_params():
    nas_lst = db.session.query(models.NasApiParams).all()
    form = forms.CreateNasApi()
    return render_template('admin_panel/admin_nas_params.html', nas_lst=nas_lst, form=form)


@app.route('/admin_panel/nas_params/add/', methods=['POST', 'GET'])
@login_required
@views_permission.admin_check
def admin_nas_add():

    form = forms.CreateNasApi()

    try:
        db.session.add(
            models.NasApiParams(
                name=form.name.data,
                ip=form.ip.data,
                port=form.port.data,
                login=form.login.data,
                passw=form.passw.data
            )
        )
        db.session.flush()
        db.session.commit()
        flash(
            message=f'SSH подключение <{form.name.data}> успешно создано в БД',
            category='notify'
        )
    except db_exc.IntegrityError:
        db.session.rollback()
        flash(
            message='Не удалось создать SSH подключение, возможно оно уже существует в БД',
            category='error'
        )
    except db_exc.SQLAlchemyError:
        db.session.rollback()
        flash(
            message='Ошибка БД. Не удалось создать SSH подключение, неивестная ошибка',
            category='error'
        )

    return redirect(url_for('admin_nas_params'))


@app.route('/admin_panel/nas_params/delete/<iid>/', methods=['POST', 'GET'])
@login_required
@views_permission.admin_check
def admin_nas_delete(iid):
    pfl = db.session.query(models.NasApiParams).get_or_404(int(iid))
    try:
        db.session.delete(pfl)
        db.session.commit()
        flash(
            message="SSH подключение к NAS серверу удалёно",
            category="notify"
        )

    except db_exc.SQLAlchemyError:
        flash(
            message="Ошибка БД. Не удалось удалить SSH подключение",
            category="error"
        )
    return redirect(url_for('admin_nas_params'))


@app.route('/admin_panel/forward_gateway/', methods=['POST', 'GET'])
@login_required
def admin_forward_gateway():
    form = forms.ChangeForwardGateway()
    params = db.session.query(models.ForwardGatewayParams).get_or_404(1)
    if request.method == 'POST':
        params.external_ip = form.external_ip.data
        params.external_port = form.external_port.data

        try:
            db.session.flush()
            db.session.commit()
            flash(message='Изменения применены', category='notify')
        except db_exc.SQLAlchemyError:
            db.session.rollback()
            flash(message='Ошибка БД. Не удалось применить изменения', category='error')

        return redirect(url_for('admin_forward_gateway'))

    form.external_ip.data = params.external_ip
    form.external_port.data = params.external_port
    return render_template('admin_panel/admin_forward_gateway.html', form=form)


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






