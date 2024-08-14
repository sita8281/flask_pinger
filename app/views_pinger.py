from app import app, forms, db, models, views_permission
from .modules import pinger
from flask import render_template, request, redirect, url_for, flash, session, abort, jsonify
from flask_login import login_required, login_user, logout_user, current_user
from datetime import timedelta, datetime
from sqlalchemy import exc as db_exc
import logging


logger = logging.getLogger('pinger')


@app.route('/pinger_panel/', methods=['GET', 'POST'])
@app.route('/pinger_panel/<folder>', methods=['GET', 'POST'])
@login_required
def main_pinger(folder=''):

    def get_hosts_dict(hosts_lst: list):
        _hosts = {}
        for host in hosts_lst:
            if host.checking == 1:
                state = 'checking'
            else:
                state = host.state
            _hosts[int(host.id)] = {
                'ip': host.ip,
                'name': host.name,
                'state': state,
                'change_state': host.change_state,
                'folder_id': host.folder_id
            }
        return _hosts

    static_folders = [
        ('all_hosts', 'All monitors', 'all'),
        ('live_hosts', 'Live monitors', 'live'),
        ('dead_hosts', 'Dead monitors', 'dead'),
        ('pause_hosts', 'Pause monitors', 'pause')
    ]

    hosts = db.session.query(models.Host).all()
    folders = db.session.query(models.HostFolder).all()

    if folder == 'all' or folder == '':
        if request.args.get('data') == 'json':
            return jsonify(get_hosts_dict(hosts))
        logger.info(f'{current_user.login}: запросил папку <id: {folder}>')
        return render_template(
            'pinger/pinger_all.html', folders=folders, hosts=hosts, static_folders=static_folders,
            current_folder=folder
        )

    if folder == 'live':
        hosts = db.session.query(models.Host).filter(models.Host.state == 'online').all()
        if request.args.get('data') == 'json':
            return jsonify(get_hosts_dict(hosts))
        logger.info(f'{current_user.login}: запросил папку <id: {folder}>')
        return render_template(
            'pinger/pinger_all.html', folders=folders, hosts=hosts, static_folders=static_folders,
            current_folder=folder
        )

    if folder == 'dead':
        hosts = db.session.query(models.Host).filter(models.Host.state == 'offline').all()
        if request.args.get('data') == 'json':
            return jsonify(get_hosts_dict(hosts))
        logger.info(f'{current_user.login}: запросил папку <id: {folder}>')
        return render_template(
            'pinger/pinger_all.html', folders=folders, hosts=hosts, static_folders=static_folders,
            current_folder=folder
        )

    if folder == 'pause':
        hosts = db.session.query(models.Host).filter(models.Host.state == 'pause').all()
        if request.args.get('data') == 'json':
            return jsonify(get_hosts_dict(hosts))
        logger.info(f'{current_user.login}: запросил папку <id: {folder}>')
        return render_template(
            'pinger/pinger_all.html', folders=folders, hosts=hosts, static_folders=static_folders,
            current_folder=folder
        )

    if folder and folder.isdigit:
        folders = db.session.query(models.HostFolder).all()
        select_folder = db.session.query(models.HostFolder).get_or_404(folder)
        if request.args.get('data') == 'json':
            return jsonify(get_hosts_dict(select_folder.hosts))
        logger.info(f'{current_user.login}: запросил папку <id: {folder}>')
        return render_template(
            'pinger/pinger_all.html', folders=folders, hosts=select_folder.hosts,
            static_folders=static_folders, current_folder=int(folder)
        )
    return abort(404)


@app.route('/pinger_panel/host_delete/<int:host>', methods=['GET'])
@login_required
@views_permission.admin_check
def delete_host(host):
    select_host = db.session.query(models.Host).get_or_404(host)
    db.session.delete(select_host)
    db.session.commit()
    logger.info(f'{current_user.login}: удалил хост <{select_host.ip}>')
    return redirect(url_for('main_pinger', folder='all'))


@app.route('/pinger_panel/folder_delete/<int:folder>', methods=['GET'])
@login_required
@views_permission.admin_check
def delete_folder(folder):
    select_folder = db.session.query(models.HostFolder).get_or_404(folder)
    child_hosts = select_folder.hosts
    for hst in child_hosts:
        db.session.delete(hst)
    db.session.delete(select_folder)
    db.session.commit()
    logger.info(f'{current_user.login}: удалил папку <{select_folder.name}>')
    return redirect(url_for('main_pinger', folder='all'))


@app.route('/pinger_panel/add_host/', methods=['GET', 'POST'])
@login_required
@views_permission.admin_check
def add_host():
    folders_lst = db.session.query(models.HostFolder).all()
    form = forms.CreateHostForm()
    if request.method == 'POST':
        try:
            db.session.add(
                models.Host(
                    name=form.name.data, ip=form.ip.data, folder_id=form.folder.data,
                    state='offline', change_state=datetime.now().strftime('%Y/%m/%d %H:%M')
                )
            )
            db.session.flush()
            db.session.commit()
            logger.info(f'{current_user.login}: добавил новый хост <{form.ip.data}> "{form.name.data}"')
            return redirect(url_for('main_pinger'))
        except db_exc.IntegrityError:
            db.session.rollback()

            logger.warning(f'{current_user.login}: не удалось добавить хост <{form.ip.data}>, IP уже есть в БД')
            flash(
                message='Хост с таким IP адресом уже существует',
                category='error'
            )

        except db_exc.SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f'{current_user.login}: не удалось добавить хост <{form.ip.data}>')
            logger.exception(e)
            flash(
                message='Не удалось добавить хост.',
                category='error'
            )

    form.folder.choices = [(fold.id, fold.name) for fold in folders_lst]
    return render_template('pinger/host_add.html', form=form)


@app.route('/pinger_panel/add_folder/', methods=['GET', 'POST'])
@login_required
@views_permission.admin_check
def add_folder():
    form = forms.CreateFolderForm()

    if request.method == 'POST':
        try:
            db.session.add(models.HostFolder(name=form.name.data))
            db.session.flush()
            db.session.commit()
            logger.info(f'{current_user.login}: создал новую папку "{form.name.data}"')
            return redirect(url_for('main_pinger'))

        except db_exc.IntegrityError:
            db.session.rollback()
            logger.warning(f'{current_user.login}: папка с названием "{form.name.data}" уже есть в БД ')
            flash(
                message='Папка с таким названием уже существует',
                category='error'
            )

        except db_exc.SQLAlchemyError as e:
            logger.error(f'{current_user.login}: не удалось создать папку "{form.name.data}"')
            logger.exception(e)
            db.session.rollback()
            flash(
                message='Не удалось добавить папку',
                category='error'
            )
    return render_template('pinger/folder_add.html', form=form)


@app.route('/pinger_panel/change_host/<int:host>', methods=['GET', 'POST'])
@login_required
@views_permission.admin_check
def change_host(host):
    folders_lst = db.session.query(models.HostFolder).all()
    form = forms.ChangeHostForm()
    host = db.session.query(models.Host).get_or_404(host)

    if request.method == 'POST' and form.is_submitted():
        try:
            host.name = form.name.data
            host.ip = form.ip.data
            host.folder_id = form.folder.data
            host.state = form.pause.data
            db.session.flush()
            db.session.commit()
            logger.info(f'{current_user.login}: изменил данные хоста <id: {host.id}>')
            return redirect(url_for('main_pinger', folder=form.folder.data))

        except db_exc.IntegrityError:
            db.session.rollback()
            logger.warning(f'{current_user.login}: присваиваемый IP уже привязан к другому хосту <id: {host.id}>')
            flash(
                message='IP адрес на который вы хотите сменить уже существует',
                category='error'
            )

        except db_exc.SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f'{current_user.login}: не удалось изменить данные хоста <id: {host.id}>')
            logger.exception(e)
            flash(
                message='Ошибка. Не удалось изменить хост',
                category='error'
            )
        _f_choices = [(fold.id, fold.name) for fold in folders_lst]
        form.folder.choices = _f_choices
        return render_template('pinger/host_change.html', form=form)

    elif request.method == 'POST' and request.form.get('pause') == '1':
        host.state = 'pause'
        try:
            db.session.flush()
            db.session.commit()
            logger.info(f'{current_user.login}: поставил хост на паузу <{host.ip}> "{host.name}"')
        except db_exc.SQLAlchemyError:
            return abort(500)
        return 'OK'

    form.ip.data = host.ip
    form.name.data = host.name
    _f_choices = [(fold.id, fold.name) for fold in folders_lst]
    form.folder.choices = _f_choices
    form.folder.data = str(host.folder_id)

    if host.state == 'pause':
        form.pause.choices = [('pause', 'Вкл'), ('offline', 'Выкл')]
    elif host.state == 'checking':
        form.pause.data = 'offline'
        flash(
            message='В данный момент хост пингуется, операции с ним невозможны',
            category='error'
        )
        return render_template('pinger/host_change.html', form=form)
    elif host.state != 'pause':
        form.pause.choices = [(host.state, 'Выкл'), ('pause', 'Вкл')]

    return render_template('pinger/host_change.html', form=form)


@app.route('/pinger_panel/change_folder/<int:folder>', methods=['GET', 'POST'])
@login_required
@views_permission.admin_check
def change_folder(folder):
    form = forms.ChangeFolderForm()
    folder = db.session.query(models.HostFolder).get_or_404(folder)

    if request.method == 'POST' and form.is_submitted():
        try:
            folder.name = form.name.data
            db.session.flush()
            db.session.commit()
            logger.info(f'{current_user.login}: изменил данные папки "{folder.name}"')
            return redirect(url_for('main_pinger'))
        except db_exc.IntegrityError:
            db.session.rollback()
            logger.warning(f'{current_user.login}: присваиваемое название уже привязано к другой папке "{folder.name}"')
            flash(
                message='Название которое вы ввели уже присвоено другой папке',
                category='error'
            )

        except db_exc.SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f'{current_user.login}: не удалось изменить данные папки "{folder.name}"')
            logger.exception(e)
            flash(
                message='Ошибка. Не удалось изменить название',
                category='error'
            )
        return render_template('pinger/host_change.html', form=form)

    form.name.data = folder.name
    return render_template('pinger/folder_change.html', form=form)


@app.route('/pinger_panel/check/<host_id>', methods=['GET', 'POST'])
@login_required
def pinger_check(host_id):
    if host_id == 'all':
        logger.info(f'{current_user.login}: запустил проверку всех хостов')
        return pinger.ping_all()
    elif host_id == 'dead':
        logger.info(f'{current_user.login}: запустил проверку мертвых хостов')
        return pinger.ping_dead()
    elif host_id.isdigit:
        return pinger.ping_one(host_id)
    abort(400)

