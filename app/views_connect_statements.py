from app import app, db, models
from flask import render_template, jsonify, request, abort, redirect, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import pickle
import logging


log = logging.getLogger('connect_statements')


@app.route('/connect_statements', methods=['GET'])
@login_required
def connect_statements():
    log.info(f'{current_user.login}: посетил страницу')
    return render_template('/connect_statements/index.html')


@app.route('/connect_statements/folder/<int:folder_id>', methods=['GET'])
@login_required
def connect_statements_list_folder(folder_id):
    statements = db.session.query(models.ConnectStatements) \
    .filter(models.ConnectStatements.folder_id == folder_id).all()
    return jsonify([statement.to_serializeble for statement in statements][::-1])


@app.route('/connect_statements/list/<endp>', methods=['GET'])
@login_required
def connect_statements_list(endp):
    if endp == 'open':
        # получить открытые и ожидающие ответа заявки
        statements = db.session.query(
            models.ConnectStatements
        ).filter(models.ConnectStatements.status >= 1).all()
        log.info(f'{current_user.login}: запросил список открытых и ожидающих ответа заявок')
    elif endp == 'close':
        # получить закрытые заявки
        statements = db.session.query(
            models.ConnectStatements
        ).filter(models.ConnectStatements.status == 0).all()
        log.info(f'{current_user.login}: запросил список закрытых заявок')
    else:
        if not endp.isdigit():
            return abort(404)
        folder_id = int(endp)
        statements = db.session.query(models.ConnectStatements) \
        .filter(models.ConnectStatements.status >= 1).filter(models.ConnectStatements.folder_id == folder_id).all()

    return jsonify([statement.to_serializeble for statement in statements][::-1])


@app.route('/connect_statements', methods=['POST'])
@login_required
def connect_statements_add():
    form = request.form
    date: str = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    messages: list = [
        {
            'sender': current_user.login,
            'date': date,
            'message': form.get('message')
        }
    ]
    db.session.add(
        models.ConnectStatements(
            name=form.get('name'),
            date=date,
            for_whom=form.get('for_whom'),
            status=1,
            messages=pickle.dumps(messages),
            for_whom_color='green',
            )
        )
    try:
        db.session.flush()
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        log.info(f'{current_user.login}: ошибка БД при создании заявки')
        return abort(500)
    log.info(f'{current_user.login}: создал новую заявку <{form.get("name")}>')
    return 'OK', 200


@app.route('/connect_statements/<int:iid>', methods=['POST', 'GET'])
@login_required
def connect_statements_resource(iid):

    statement = db.session.query(models.ConnectStatements).get_or_404(iid)
    if request.method == 'GET':
        messages: list = pickle.loads(statement.messages)
        log.info(f'{current_user.login}: запросил данные заявки <{statement.name}> | <id={statement.id}>')
        return jsonify({
            'messages': messages,
            'name': statement.name,
            'status': statement.status,
            'for_whom': statement.for_whom,
            'folder_id': statement.folder_id
        })
    form = request.form

    if form.get('message'):
        date: str = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        messages: list = pickle.loads(statement.messages)
        messages.append({'sender': current_user.login, 'date': date, 'message': form['message']})
        statement.messages = pickle.dumps(messages)
        log.info(f'{current_user.login}: отправил сообщение <{form["message"]}>'
                 f' в заявку <{statement.name}> | <id={statement.id}>')
    if form.get('status'):
        statement.status = int(form['status'])
    if form.get('for_whom'):
        statement.for_whom = form['for_whom']
    if form.get('for_whom_color'):
        statement.for_whom_color = form['for_whom_color']
    if form.get('folder_id'):
        statement.folder_id = form['folder_id']
    try:
        db.session.flush()
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return abort(500)
    return 'OK', 200


@app.route('/connect_statements/replace', methods=['POST'])
@login_required
def statements_replace():
    stmts = db.session.query(models.ConnectStatements).filter(models.ConnectStatements.status >= 1).all()
    drag = request.form.get('drag')
    drop = request.form.get('drop')
    if 'id' in drag and 'sep' in drop:
        drag_id = int(drag.split('-')[1].strip())
        drop_id = int(drop.split('-')[1].strip())

        if drag_id > drop_id:
            for i in reversed(range(len(stmts))):
                if stmts[i].id < drag_id:
                    stmts[i+1].lst, stmts[i].lst = stmts[i].lst, stmts[i+1].lst
                if stmts[i].id == drop_id:
                    break

        if drag_id < drop_id:
            for i in range(len(stmts)):
                if stmts[i].id > drag_id:
                    stmts[i-1].lst, stmts[i].lst = stmts[i].lst, stmts[i-1].lst
                if stmts[i].id == drop_id:
                    break
    try:
        db.session.flush()
        db.session.commit()
    except SQLAlchemyError:
        return abort(500)

    return 'OK', 200

@app.route('/connect_statements/folders', methods=['POST'])
@login_required
def statement_create_folder():
    name = request.form.get('name')
    if not name:
        return abort(400)
    
    db.session.add(models.StatementsFolder(name=name))
    try:
        db.session.flush()
        db.session.commit()
        return 'OK', 200
    except SQLAlchemyError:
        return 'error', 200
    
@app.route('/connect_statements/folders', methods=['GET'])
@login_required
def statement_get_folder() -> list[dict]:
    folders = db.session.query(models.StatementsFolder).all()
    return jsonify([{'id': f.id, 'name': f.name} for f in folders]), 200


@app.route('/connect_statements/folders/<int:folder>', methods=['GET'])
@login_required
def statement_folder_delete(folder: int):
    f = db.session.query(models.StatementsFolder).get_or_404(folder)
    db.session.delete(f)
    db.session.commit()
    return redirect(url_for('connect_statements'))