from .modules import nas_poller, dumper_sw
from app import models, db, app
from flask import jsonify, request, abort, render_template, redirect, url_for
from flask_login import current_user
import pickle
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc
import logging


logger = logging.getLogger('search_port')


@app.route('/search_port/search_login/', methods=['GET'])
def search_port_login():
    """Первичная страница. Поиск по логину"""
    login = request.args.get('login')
    logger.info(f'{current_user.login}: зашел на страницу поиска по логину')
    return render_template('search_port_panel/login.html', login=login)


@app.route('/search_port/search_mac/', methods=['GET'])
def search_port_mac():
    """Страница поиска по MAC"""
    logger.info(f'{current_user.login}: зашел на страницу поиска по MAC')
    return render_template('search_port_panel/mac.html')


@app.route('/search_port/list_sw/', methods=['GET'])
def search_port_list_sw():
    """Страница списка SW-dumps"""
    lst = [{'id': i.id, 'date': i.date, 'len': len(i.dump)} for i in db.session.query(models.SwDumps).all()]
    logger.info(f'{current_user.login}: запросил список всех записей Switches')
    return render_template('search_port_panel/sw_dumps.html', lst=lst)


@app.route('/search_port/list_nas/', methods=['GET'])
def search_port_list_nas():
    """Страница списка NAS-dumps"""
    lst = [{'id': i.id, 'date': i.date, 'len': len(i.dump)} for i in db.session.query(models.NasDumps).all()]
    logger.info(f'{current_user.login}: запросил список всех записей NAS-servers')
    return render_template('search_port_panel/nas_dumps.html', lst=lst)


@app.route('/search_port/dump/', methods=['GET'])
def search_port_recv_dump():
    """Страница выбора DUMP"""
    logger.info(f'{current_user.login}: зашёл на страницу снятия DUMPs')
    return render_template('search_port_panel/dump.html')


@app.route('/search_port/dump_sw/', methods=['POST'])
def search_port_dump_sw():
    """Rest запрос для создания новой записи SW"""
    if dumper_sw.run_dump():
        logger.info(f'{current_user.login}: запустил процесс снятия новой записи всех Switches')
        return jsonify({'status': 'ok'})
    logger.warning(f'{current_user.login}: прервана попытка запуска записи всех Switches, так как процесс уже запущен')
    return jsonify({'status': 'busy'})


@app.route('/search_port/dump_nas/', methods=['POST'])
def search_port_dump_nas():
    """Rest запрос для создания новой записи NAS"""
    try:
        db.session.add(models.NasDumps(
            date=datetime.now().strftime('%Y/%m/%d %H:%M'),
            dump=pickle.dumps(nas_poller.get_multiple_sessions())
        ))
        db.session.flush()
        db.session.commit()
        logger.info(f'{current_user.login}: новая запись NAS добавлена в базу данных')
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'{current_user.login}: не удалось добавить новую запись в базу данных')
        logger.exception(e)
        return jsonify({'status': 'db error'})

    return jsonify({'status': 'ok'})


@app.route('/search_port/dump_check/', methods=['POST'])
def search_port_dump_check():
    """Rest запрос для проверки, снимается ли в данный момент DUMP или нет"""
    return jsonify(dumper_sw.is_busy())


@app.route('/search_port/delete_sw/<int:iid>/', methods=['POST', 'GET'])
def search_port_delete_sw(iid):
    """Rest запрос на удаление sw-dump записи в БД, по id"""
    dump = db.session.query(models.SwDumps).get_or_404(iid)
    db.session.delete(dump)
    db.session.commit()
    logger.info(f'{current_user.login}: удалил запись SW из базы данных <id: {iid}>')
    return redirect(url_for('search_port_list_sw'))


@app.route('/search_port/delete_nas/<int:iid>/', methods=['POST', 'GET'])
def search_port_delete_nas(iid):
    """Rest запрос на удаление nas-dump записи в БД, по id"""
    dump = db.session.query(models.NasDumps).get_or_404(iid)
    db.session.delete(dump)
    db.session.commit()
    logger.info(f'{current_user.login}: удалил запись NAS из базы данных <id: {iid}>')
    return redirect(url_for('search_port_list_nas'))


@app.route('/search_port/get_nas/<int:iid>/', methods=['POST'])
def search_port_get_nas(iid):
    """Rest запрос для получения данных записи"""
    row = db.session.query(models.NasDumps).get_or_404(iid)
    logger.info(f'{current_user.login}: запросил данные NAS записи <id: {row.id}>, <дата создания: {row.date}>')
    return jsonify({
        'id': row.id,
        'date': row.date,
        'dump': pickle.loads(row.dump)
    })


@app.route('/search_port/get_sw/<int:iid>/', methods=['POST'])
def search_port_get_sw(iid):
    """Rest запрос для получения данных записи"""
    row = db.session.query(models.SwDumps).get_or_404(iid)
    logger.info(f'{current_user.login}: запросил данные SW записи <id: {row.id}>, <дата создания: {row.date}>')
    return jsonify({
        'id': row.id,
        'date': row.date,
        'dump': pickle.loads(row.dump)
    })


@app.route('/search_port/search/', methods=['POST'])
def search_port_login_run():
    """Rest запрос на поиск по логину"""

    single = False
    mac = request.form.get('mac')
    login = request.form.get('login')

    search_result_list = []

    if request.form.get('single'):
        single = True
        nas_dumps = [db.session.query(models.NasDumps).order_by(desc(models.NasDumps.id)).first()]
        sw_dumps = [db.session.query(models.SwDumps).order_by(desc(models.SwDumps.id)).first()]
    else:
        nas_dumps = db.session.query(models.NasDumps).all()
        sw_dumps = db.session.query(models.SwDumps).all()

    for nas_dump in nas_dumps:
        if login:
            mac = pickle.loads(nas_dump.dump).get(login)
            if not mac:
                continue
        elif mac:
            _login = [login for login, _mac in pickle.loads(nas_dump.dump).items() if mac == _mac]
            if not _login:
                continue
            login = _login[0]

        else:
            return abort(400)

        layer_nas = {'id': nas_dump.id, 'date': nas_dump.date, 'mac': mac, 'login': login, 'sw_dumps': []}
        for sw_dump in sw_dumps:
            sw_searched_list = []
            sw_list = pickle.loads(sw_dump.dump)
            for sw in sw_list:
                port = sw['ports'].get(mac)
                if port:
                    sw_searched_list.append({
                        'port': port,
                        'host': sw['host'],
                        'name': sw['name'],
                        'device': sw['device']
                    })
            if sw_searched_list:
                layer_nas['sw_dumps'].append({'id': sw_dump.id, 'date': sw_dump.date, 'sw_list': sw_searched_list})

        search_result_list.append(layer_nas)

    if not search_result_list:
        if not mac:
            logger.info(f'{current_user.login}: не удалось найти пользователя с логином: <{login}>')
        else:
            logger.info(f'{current_user.login}: не удалось найти пользователя с MAC: <{mac}>')
        return abort(404)

    logger.info(f'{current_user.login}: успешно найден пользователь с логином: <{login}>')
    if request.form.get('json'):
        return jsonify(search_result_list)

    if single:
        return render_template('search_port_panel/result_single.html', result=search_result_list)
    else:
        return render_template('search_port_panel/result_list.html', result=search_result_list)
