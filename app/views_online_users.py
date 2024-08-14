from app import app, forms, db, models, views_permission
from flask import render_template, request, redirect, url_for, flash, session, send_file, jsonify, abort
from flask_login import login_required, login_user, logout_user, current_user
from .modules import sessions_online


@app.route('/connected', methods=['POST'])
@login_required
def is_online():
    host = request.headers.get('X-Real-Ip')
    if not host:
        host = request.remote_addr

    signal = sessions_online.connect(
        session_token=request.cookies.get('session'),
        remote_ip=host,
        login=current_user.login
    )
    if signal:
        return signal, 200
    return 'empty', 200


@app.route('/online_users', methods=['GET'])
@login_required
def users_online():
    return jsonify(sessions_online.get_connections), 200


@app.route('/disconnect', methods=['POST'])
@login_required
def user_disconnect():
    user_login = request.form.get('login')
    user_id = request.form.get('id')
    if not user_login or not user_id:
        return jsonify('notify', 'Вы прислали пустой запрос')
    if user_login == current_user.login:
        sessions_online.logout_signal(user_id)
        return jsonify('notify', 'Сигнал на разрыв сессии отправлен')
    if current_user.privilege == 'admin':
        sessions_online.logout_signal(user_id)
        return jsonify('notify', 'Сигнал на разрыв сессии отправлен')
    else:
        return jsonify(
            'notify', 'Не достаточно прав для разрыва чужой сессии, вы можете разрывать только сессии вашего аккаунта'
        )

