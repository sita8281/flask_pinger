from app import app, db, models
from .deil_api_context import DeilContext
from .modules import nas_poller
from flask import render_template, request, abort, jsonify
from flask_login import login_required, current_user
import pickle
import time
import logging


logger = logging.getLogger('carbon')


@app.route('/carbon/', methods=['GET'])
@login_required
def carbon_main():
    all_tree = db.session.query(models.CarbonApiData).get_or_404(1).data
    logger.info(f'{current_user.login}: посетил Carbon страницу')
    login = ''
    params = None
    if request.args.get('create_statement'):
        params = 'create_statement'
    if request.args.get('login'):
        login = request.args.get('login')
    return render_template(
        'carbon_panel/carbon.html',
        tree=pickle.loads(all_tree),
        params=params,
        login=login
    )


@app.route('/carbon/info/', methods=['GET'])
@login_required
def carbon_info():
    with DeilContext() as deil_api:
        info = deil_api.get_info_user(iid=request.args.get('iid'))
    if not info:
        return abort(404)

    for c, inf in enumerate(info):
        if c % 2 == 0:
            inf.append(0)
        else:
            inf.append(1)

    logger.info(f'{current_user.login}: запросил данные пользователя <iid: {request.args.get("iid")}>')

    return render_template(
        'carbon_panel/carbon_info.html',
        info=info,
        date=time.strftime('%Y-%m-%d', time.gmtime()),
        id_user=request.args.get('iid')
    )


@app.route('/carbon/sessions/', methods=['GET'])
@login_required
def carbon_sessions():
    with DeilContext() as deil_api:
        sessions = deil_api.get_sessions_user(
            iid=request.args.get('iid'),
            start_date=request.args.get('first'),
            end_date=request.args.get('end')
        )

    logger.info(f'{current_user.login}: запросил статистику пользователя <iid: {request.args.get("iid")}>')

    return render_template('carbon_panel/carbon_sessions.html', sessions=sessions)


@app.route('/carbon/pppoe/<value>/', methods=['GET'])
@login_required
def carbon_pppoe(value):
    if value == 'all':
        logins_lst = [key for key in nas_poller.get_multiple_sessions().keys()]
        logger.info(f'{current_user.login}: запросил полный список активных PPPoE сессий')
        return jsonify({
            'response': logins_lst
        })
    elif value == 'one':
        finded = nas_poller.find_session_by_login(login=request.args.get('login'))
        logger.info(f'{current_user.login}: запросил состояние PPPoE сессии <{request.args.get("login")}>')
        if finded:
            return jsonify({'status': True})
        else:
            return jsonify({'status': False})



