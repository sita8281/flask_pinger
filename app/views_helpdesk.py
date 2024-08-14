from app import app, db, models
from .deil_api_context import DeilContext
from flask import render_template, request, abort, jsonify, url_for
from flask_login import login_required, current_user
import pickle
import collections
import re
import logging


logger = logging.getLogger('helpdesk')


@app.route('/helpdesk/', methods=['GET'])
@login_required
def helpdesk_main():
    logger.info(f'{current_user.login}: посетил Helpdesk страницу')
    return render_template('helpdesk_panel/helpdesk.html')


@app.route('/helpdesk/loading/', methods=['GET'])
@login_required
def helpdesk_loading():
    return render_template('helpdesk_panel/loading.html')


@app.route('/helpdesk/loading_err/', methods=['GET'])
@login_required
def helpdesk_loading_err():
    return render_template('helpdesk_panel/loading_err.html')


@app.route('/helpdesk/helpdesk_add/', methods=['GET'])
@login_required
def helpdesk_add():
    return render_template('helpdesk_panel/helpdesk.html')


@app.route('/helpdesk/helpdesk_list/', methods=['GET'])
@login_required
def helpdesk_list():
    ticket = collections.namedtuple('Ticket', ['id', 'info', 'date', 'state'])
    new_lst = []
    with DeilContext() as deil_api:
        lst = deil_api.get_helpdesk_list()
    if not lst:
        logger.warning(f'{current_user.login}: не удалось получить список заявок')
        return abort(404, 'Deil API Gateway: 192.168.255.100 отдал необрабатываемый ответ')

    for item, val in lst.items():
        n, d, s = val
        new_lst.append(
            ticket(id=item, date=d, state=s, info=n)
        )
    logger.info(f'{current_user.login}: запросил список заявок')
    return render_template('helpdesk_panel/helpdesk_list.html', lst=new_lst)


@app.route('/helpdesk/helpdesk_chat/', methods=['GET'])
@login_required
def helpdesk_chat():
    def filter_phone_number(s):
        try:
            r = re.search(r'(\+)?((\d{2,3}) ?\d|\d)(([ -]?\d)|( ?(\d{2,3}) ?)){5,12}\d', s)
            r = r.group().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if len(r) == 10:
                r = '+7' + r
            elif len(r) > 10:
                r = '+7' + r[1:]
        except Exception:
            return
        return r

    def filter_address(s):
        try:
            s = s.split(' ')[:-2]
            addr = ' '.join(s)
            dump = db.session.query(models.CarbonApiData).get_or_404(1).data

            for tree in pickle.loads(dump):
                try:
                    for ch in tree['child']:
                        if addr.strip() == ch['name'].strip():
                            return {'login': ch['login'], 'href': url_for('carbon_main', login=ch["name"]),
                                    'name': ch['name']}
                except KeyError:
                    pass
        except Exception:
            pass
        return {'login': 'not found', 'href': './html/carbon.html'}

    if not request.args.get('id'):
        return render_template('helpdesk_panel/helpdesk_chat.html', test='none')
    iid = request.args.get('id')
    if 'redirect' in request.args:
        redirect = True
    else:
        redirect = ''

    with DeilContext() as deil_api:
        result = deil_api.get_helpdesk_info(iid=iid)
    first_string_chat = result['chat'][0][0]
    address_data_time = result['chat'][0][1]
    result['iid_'] = iid

    search_info = {'login': 'not found', 'href': url_for('search_port_login')}
    addr_login = filter_address(address_data_time)
    if addr_login['login'] != 'not found':
        search_info['login'] = addr_login['login']
        search_info['href'] = url_for('search_port_login', login=addr_login["name"])

    logger.info(f'{current_user.login}: посетил заявку <{iid}>')

    return render_template(
        'helpdesk_panel/helpdesk_chat.html',
        data=result,
        phone_number=filter_phone_number(first_string_chat),
        redirect=redirect,
        carbon=addr_login,
        search_port=search_info
    )


@app.route('/helpdesk/helpdesk_folders/', methods=['GET'])
@login_required
def helpdesk_folders():
    with DeilContext() as deil_api:
        result = deil_api.get_folders()
    return render_template('helpdesk_panel/helpdesk_folders.html', folders=result)


@app.route('/helpdesk/helpdesk_users/', methods=['GET'])
@login_required
def helpdesk_users():
    with DeilContext() as deil_api:
        result = deil_api.get_users()
    return render_template('helpdesk_panel/helpdesk_users.html', users=result)


@app.route('/helpdesk/helpdesk_form/', methods=['GET'])
@login_required
def helpdesk_form():
    return render_template('helpdesk_panel/helpdesk_form.html', iid=request.args.get('iid'))


@app.route('/helpdesk/create/', methods=['GET'])
@login_required
def helpdesk_create():
    try:
        with DeilContext() as deil_api:
            deil_api.create_helpdesk(request.args.get('iid').strip(), request.args.get('subj'), request.args.get('info'))
            return jsonify({'success': 'statement created'})
    except Exception as helpdesk_err:
        return jsonify({'error': str(helpdesk_err)})


@app.route('/helpdesk/close/', methods=['GET'])
@login_required
def helpdesk_close():
    vals = list(request.args.values())
    try:
        with DeilContext() as deil_api:
            deil_api.close_helpdesk(*vals)
        logger.info(f'{current_user.login}: закрыл заявки {vals}')
        return jsonify({'success': 'statement deleted'})
    except Exception as helpdesk_err:
        logger.error(f'{current_user.login}: не удалось закрыть заявки')
        logger.exception(helpdesk_err)
        return jsonify({'error': str(helpdesk_err)})


@app.route('/helpdesk/send/', methods=['GET'])
@login_required
def helpdesk_send():
    try:
        with DeilContext() as deil_api:
            deil_api.send_helpdesk(request.args.get('iid'), request.args.get('text'))
        logger.info(
            f'{current_user.login}: добавил сообщение <{request.args.get("text")}> к заявке <{request.args.get("iid")}>'
        )
        return jsonify({'success': 'message sended'})
    except Exception as helpdesk_err:
        logger.error(f'{current_user.login}: не удалось добавить сообщение к заявке <{request.args.get("iid")}>')
        logger.exception(helpdesk_err)
        return jsonify({'error': str(helpdesk_err)})


