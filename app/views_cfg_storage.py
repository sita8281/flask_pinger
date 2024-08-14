from flask import request, render_template, redirect, url_for, abort, flash, send_file
from flask_login import current_user, login_required
from app import app, models, db
from datetime import datetime
import sqlalchemy.exc as db_exc
import io
import logging

log = logging.getLogger('config_storage')


@app.route('/cfg/', methods=['GET'])
def configs():
    cfgs = db.session.query(models.ConfigStorage).all()
    action = request.args.get('action')
    log.info(f'{current_user.login}: посетил страницу')
    return render_template('cfg_storage/index.html', action=action, cfgs=cfgs, current_cfg=None)


@app.route('/cfg/<int:iid>', methods=['GET'])
def config(iid: int):
    current_cfg = db.session.query(models.ConfigStorage).get_or_404(iid)
    cfgs = db.session.query(models.ConfigStorage).all()

    if request.args.get('download'):
        file_data = io.BytesIO(current_cfg.text.encode('utf-8'))
        log.info(f'{current_user.login}: начал скачивание файла <{current_cfg.name}.txt>')
        return send_file(
            file_data, max_age=0, download_name=f'{current_cfg.name}.txt', mimetype='application/octet-stream'
        )

    log.info(f'{current_user.login}: запросил конфиг <{current_cfg.name}>')
    return render_template('cfg_storage/index.html', cfgs=cfgs, current_cfg=current_cfg)


@app.route('/cfg/<int:iid>', methods=['POST'])
def update_config(iid: int):
    name = request.form.get('name')
    cfg_text = request.form.get('cfg')

    if not all((name, cfg_text)):
        abort(400)

    cfg = db.session.query(models.ConfigStorage).get_or_404(iid)
    cfg.name = name
    cfg.text = cfg_text

    try:
        db.session.flush()
        db.session.commit()
        log.info(f'{current_user.login}: отредактировал конфиг <{cfg.name}>')
        flash(message=f'Конфиг "{cfg.name}" отредактирован', category='success')
    except db_exc.SQLAlchemyError:
        db.session.rollback()
        flash(message='Ошибка БД, не удалось изменить конфиг', category='error')
        log.info(f'{current_user.login}: не удалось отредактировать <{cfg.name}>, из за ошибки БД')
        return redirect(url_for('configs', action='new'))
    return redirect(url_for('config', iid=cfg.id))


@app.route('/cfg/del/<int:iid>', methods=['POST', 'GET'])
def delete_config(iid):
    cfg = db.session.query(models.ConfigStorage).get_or_404(iid)
    db.session.delete(cfg)
    db.session.commit()
    flash(message=f'Конфиг "{cfg.name}" успешно удалён', category='success')
    log.info(f'{current_user.login}: удалил конфиг <{cfg.name}> | <id={cfg.id}>')
    return redirect(url_for('configs'))


@app.route('/cfg/add', methods=['POST'])
def create_config():
    name = request.form.get('name')
    cfg = request.form.get('cfg')

    if not all((name, cfg)):
        abort(400)
    cfg_model = models.ConfigStorage(name=name, text=cfg, date=datetime.now().strftime('%Y/%m/%d %H:%M'))
    db.session.add(cfg_model)
    try:
        db.session.flush()
        db.session.commit()
        flash(message='Новый конфиг успешно создан', category='success')
        log.info(f'{current_user.login}: создал новый конфиг <{cfg_model.name}>')
    except db_exc.SQLAlchemyError:
        db.session.rollback()
        flash(message='Ошибка БД, не удалось добавить конфиг', category='error')
        log.info(f'{current_user.login}: не удалось создать новый конфиг, из за ошибки БД')
        return redirect(url_for('configs', action='new'))

    return redirect(url_for('config', iid=cfg_model.id))
