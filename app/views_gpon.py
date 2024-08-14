from app import app, db, models, views_permission
from .modules import gpon_api, nas_poller
from flask import render_template, request, abort, jsonify
from flask_login import login_required, current_user
from types import SimpleNamespace
import logging
from threading import Thread


logger = logging.getLogger('gpon')


@app.route('/gpon_panel/', methods=['GET'])
@login_required
def gpon_panel():
    logger.info(f'{current_user.login}: посетил страницу')
    try:
        return render_template('/gpon_panel/gpon_panel.html', onu_data=SimpleNamespace(**request.args))
    except KeyError:
        return render_template('/gpon_panel/gpon_panel.html', onu_data=None)


@app.route('/gpon_panel/register/', methods=['GET'])
@login_required
def gpon_register():
    logger.info(f'{current_user.login}: посетил страницу регистрации ONT')
    return render_template('/gpon_panel/register.html')


@app.route('/gpon_panel/register_manual/', methods=['GET'])
@login_required
def gpon_register_manual():
    logger.info(f'{current_user.login}: посетил страницу ручной регистрации ONT')
    pfls = db.session.query(models.GponProfiles).all()

    return render_template('/gpon_panel/register_manual.html', profiles=pfls)


@app.route('/gpon_panel/onu_info_render/', methods=['POST'])
@login_required
def onu_info_render():
    args = (
        request.form["gpon"],
        request.form["slot"],
        request.form["port"],
        request.form["iid"],
    )
    logger.info(f'{current_user.login}: запросил данные ONT, {args}')
    return render_template('/gpon_panel/ont_info.html', args=args)


@app.route('/gpon_panel/mac/', methods=['GET'])
@login_required
def gpon_mac_page():
    logger.info(f'{current_user.login}: посетил страницу MAC-table')
    return render_template('/gpon_panel/mac_page.html')


@app.route('/gpon_panel/service_ports/', methods=['GET'])
@login_required
def gpon_service_ports_page():
    logger.info(f'{current_user.login}: посетил страницу Service-ports-table')
    return render_template('/gpon_panel/service_ports_page.html')


@app.route('/gpon_panel/signals_page/', methods=['GET'])
@login_required
def gpon_signals_page():
    logger.info(f'{current_user.login}: посетил страницу Signals-table')
    return render_template('/gpon_panel/signal_panel.html')


@app.route('/gpon_panel/sn_page/', methods=['GET'])
@login_required
def gpon_sn_page():
    logger.info(f'{current_user.login}: посетил страницу поиска ONT по SN')
    return render_template('/gpon_panel/sn_panel.html')


@app.route('/gpon_panel/traffic_page/', methods=['GET'])
@login_required
def gpon_traffic_page():
    logger.info(f'{current_user.login}: посетил страницу отображения трафика')
    return render_template('/gpon_panel/traffic_panel.html')


@app.route("/gpon_panel/onu_list/", methods=['POST'])
@login_required
def onu_list():
    r = gpon_api.onu_list(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"]
    )
    logger.info(f'{current_user.login}: запросил список ONT, {dict(request.form)}')
    return jsonify(r)


@app.route("/gpon_panel/onu_info/", methods=['POST'])
@login_required
def onu_info():
    r = gpon_api.onu_info_simple(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        iid=request.form["iid"]
    )
    logger.info(f'{current_user.login}: запросил информацию ONT, {dict(request.form)}')
    return jsonify(r)


@app.route("/gpon_panel/onu_optical_info/", methods=['POST'])
@login_required
def onu_optical_info():
    r = gpon_api.onu_optical_info_simple(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        iid=request.form["iid"]
    )
    logger.info(f'{current_user.login}: запросил оптическую информацию ONT, {dict(request.form)}')
    return jsonify(r)


@app.route("/gpon_panel/ping/", methods=["POST"])
@login_required
def optical_ping():
    r = gpon_api.optical_ping(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        onu_id=request.form["onu_id"],
    )
    # logger.info(f'{current_user.login}: оптический ping-запрос, {request.form}')
    return jsonify(r)


@app.route("/gpon_panel/autofind/<gpon>", methods=["POST"])
@login_required
def autofind_gpon(gpon):
    if gpon == 'garage':
        slots = {'0/0': 8, '0/1': 8}
    elif gpon == 'etag':
        slots = {'0/1': 16}
    else:
        return abort(400)

    finded_ont = []

    for slot in slots:
        for port in range(slots[slot]):
            r = gpon_api.auto_find(gpon=gpon, slot=slot, port=str(port))
            for ont in r:
                finded_ont.append(ont)
    logger.info(f'{current_user.login}: выполнил авто-поиск на GPON-блоке: <{gpon}>')
    return jsonify(finded_ont)


@app.route("/gpon_panel/get_profiles/", methods=["POST"])
@login_required
def gpon_profiles():
    pfls = db.session.query(models.GponProfiles).all()
    if not pfls:
        return abort(404)
    pfls = [(pfl.id, pfl.name) for pfl in pfls]
    logger.info(f'{current_user.login}: запросил список Vlan-профилей')
    return jsonify(pfls)


@app.route("/gpon_panel/register/", methods=["POST"])
@login_required
def register_onu():
    ont_model = request.form["model"]
    pfl_id = request.form["pfl_id"]
    pfl = db.session.query(models.GponProfiles).get_or_404(int(pfl_id))

    r = gpon_api.register_onu(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        name=request.form["name"],
        sn=request.form["sn"],
        srv_profile=pfl.srv_profile,
        line_profile=pfl.line_profile
    )

    ont_id = r.get("onu_id")
    if not ont_id:
        return jsonify(r)

    r = gpon_api.next_free_index(gpon=request.form["gpon"])
    srv = r.get("Next valid free service virtual port ID")
    if not srv:
        return jsonify(srv)

    r = gpon_api.add_srv_port(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        onu_id=ont_id,
        gem=pfl.gemport,
        vlan=pfl.vlan,
        service_port=srv
    )
    if not r.get("success"):
        return jsonify(r)

    if ont_model.find("310") != -1:
        r = gpon_api.native_vlan(
            gpon=request.form["gpon"],
            slot=request.form["slot"],
            port=request.form["port"],
            onu_id=ont_id,
            vlan=pfl.vlan
        )
        if not r.get("success"):
            logger.info(f'{current_user.login}: частично зарегистрировал ONT "{request.form["name"]}"')
            return jsonify({"error": "ONT частично зарегистрированна. Не удалось привязать Native VLAN"})

    logger.info(f'{current_user.login}: успешно зарегистрировал  ONT "{request.form["name"]}"')
    return jsonify({"success": "ONT успешно зарегистрированна."})


@app.route("/gpon_panel/register_manual/", methods=["POST"])
@login_required
def register_onu_manual():
    ont_model = request.form["model"]
    pfl_id = request.form["pfl_id"]
    pfl = db.session.query(models.GponProfiles).get_or_404(int(pfl_id))

    r = gpon_api.register_onu_manual(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        name=request.form["name"],
        sn=request.form["sn"],
        srv_profile=pfl.srv_profile,
        line_profile=pfl.line_profile
    )

    ont_id = r.get("onu_id")
    if not ont_id:
        return jsonify(r)

    r = gpon_api.next_free_index(gpon=request.form["gpon"])
    srv = r.get("Next valid free service virtual port ID")
    if not srv:
        return jsonify(srv)

    r = gpon_api.add_srv_port(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        onu_id=ont_id,
        gem=pfl.gemport,
        vlan=pfl.vlan,
        service_port=srv
    )
    if not r.get("success"):
        return jsonify(r)

    if ont_model.find("310") != -1:
        r = gpon_api.native_vlan(
            gpon=request.form["gpon"],
            slot=request.form["slot"],
            port=request.form["port"],
            onu_id=ont_id,
            vlan=pfl.vlan
        )
        if not r.get("success"):
            logger.info(f'{current_user.login}: частично зарегистрировал ONT "{request.form["name"]}"')
            return jsonify({"error": "ONT частично зарегистрированна. Не удалось привязать Native VLAN"})

    logger.info(f'{current_user.login}: успешно зарегистрировал  ONT "{request.form["name"]}"')
    return jsonify({"success": "ONT успешно зарегистрированна."})


@app.route("/gpon_panel/delete/", methods=["POST"])
@login_required
def delete_onu():

    r = gpon_api.service_port_list(gpon=request.form["gpon"])
    if isinstance(r, list):
        for srv_data in r:
            if srv_data["onu_id"] != request.form["onu_id"]:
                continue
            if srv_data["port"] != request.form["port"]:
                continue
            if srv_data["slot"] != request.form["slot"]:
                continue

            gpon_api.undo_srv_port(gpon=request.form["gpon"], service_port=srv_data["service_port"])
            break

    r = gpon_api.delete_onu(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        onu_id=request.form["onu_id"],
    )

    if r.get('success'):
        logger.info(f'{current_user.login}: удалил ONT {dict(request.form)}')
        return jsonify({"success": "ONT успешно удалена."})
    logger.warning(f'{current_user.login}: возникли проблемы при удалении ONT {dict(request.form)}')
    return jsonify(r)


@app.route('/gpon_panel/mac/<gpon>', methods=['POST'])
@login_required
def gpon_mac_all(gpon):
    logger.info(f'{current_user.login}: запросил список MAC-адресов на GPON-блоке <{gpon}>')
    return jsonify(lst=gpon_api.mac_all(gpon))


@app.route('/gpon_panel/service_ports/<gpon>', methods=['POST'])
@login_required
def gpon_service_port_all(gpon):
    logger.info(f'{current_user.login}: запросил список Service-ports на GPON-блоке <{gpon}>')
    return jsonify(lst=gpon_api.service_port_list(gpon))


@app.route('/gpon_panel/traffic/<method>', methods=['POST'])
@login_required
def gpon_traffic(method):
    if method == "vlan":
        result = gpon_api.traffic_vlan(
            gpon=request.form['gpon'],
            vlan=request.form['vlan']
        )

    elif method == "port":
        result = gpon_api.traffic_port(
            gpon=request.form['gpon'],
            port=request.form['port'],
            slot=request.form['slot']
        )
    else:
        return abort(404)
    return jsonify(result)


@app.route('/gpon_panel/mac_onu/', methods=['POST'])
@login_required
def gpon_find_mac():
    output = []
    r = gpon_api.mac_onu_port(
        gpon=request.form["gpon"],
        slot=request.form["slot"],
        port=request.form["port"],
        onu_id=request.form["onu_id"],
    )
    if 'error' in r:
        return jsonify(r)

    for mac in r:
        output.append([mac, nas_poller.find_session_by_mac(mac=mac)])
    logger.info(f'{current_user.login}: запросил PPPoE-сессию {dict(request.form)}')
    return jsonify(output)


@app.route('/gpon_panel/save/', methods=['POST'])
@login_required
def gpon_save_config():
    gpon_api.save_config_thread()
    logger.info(f'Пользователь <{current_user.login}> сохранил конфигурации.')
    return jsonify('Конфигурация сохранена.')
