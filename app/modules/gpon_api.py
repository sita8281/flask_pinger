from .telnet_socket import TelnetGponExec
from app import db, models, app
from threading import Thread
import re


def failure_parser(lines):
    for line in lines:
        if "Failure" in line:
            fail, error = line.split(":", 1)
            return {fail.strip(): error.strip()}


def normalize(string, del_separators=False, striped=True):
    del_sep_flag = False
    lines = []
    for line in string.split("\n"):
        if "-" * 5 in line and del_separators:
            if not del_sep_flag:
                del_sep_flag = True
            elif del_sep_flag:
                del_sep_flag = False
            continue

        elif del_sep_flag:
            continue

        if "---- More" in line[:10]:
            if striped:
                lines.append(line[86:].strip())
            else:
                lines.append(line[84:])
        else:
            if striped:
                lines.append(line.strip())
            else:
                lines.append(line)
    return lines


def info_parser(lst):
    fl = False
    new_lst = {}

    for line in lst:
        if "-"*5 in line:
            fl = not fl
            continue
        if fl:
            try:
                key, val = line.split(':', 1)
                new_lst[key.strip()] = val.strip()
            except ValueError:
                break
    return new_lst


def gpon_connection(type_gpon):
    with app.app_context():
        gpon_blocks = db.session.query(models.GponParams).all()

        for block in gpon_blocks:
            if block.tag == type_gpon:
                return TelnetGponExec(
                    login=block.login, password=block.passw, host=(block.ip, block.port)
                )
        else:
            return


def onu_list(gpon, slot, port):
    """
    Получить список ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"display ont info {port} all\n",
        " " * 12 + "\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=10)
    if error:
        return {"error": error}
    lst = []
    try:
        for i in normalize(data):
            onu_id = i[8:-61].strip()
            onu_sn = i[12:-42].strip()
            onu_state = i[43:-20].strip()
            if onu_id.isdigit():
                lst.append({"gpon": gpon, "id": onu_id, "sn": onu_sn, "name": "", "port": port, "slot": slot,
                            "state": onu_state})
                continue

            onu_id = i[10:15].strip()
            if onu_id.isdigit():
                onu_name = i[15:].strip()
                for index_onu in range(len(lst)):
                    if lst[index_onu]["id"] == onu_id:
                        lst[index_onu]["name"] = onu_name
        return lst
    except Exception as e:
        return {"error": str(e)}


def onu_info(gpon, slot, port, iid):
    """
    Получить информацию об ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"display ont info {port} {iid}\n",
        5*"\n" + "q"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}
    try:
        return info_parser(normalize(data))
    except Exception as e:
        return {"error": str(e)}


def onu_info_simple(gpon, slot, port, iid):
    """
    Получить урезанную информацию об ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"display ont info {port} {iid}\n",
        5*"\n" + "q"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}
    try:
        info = info_parser(normalize(data))
        simple_info = {
            'Description': info.get('Description'),
            'Last down time': info.get('Last down time'),
            'Last dying gasp time': info.get('Last dying gasp time'),
            'Last up time': info.get('Last up time'),
            'ONT online duration': info.get('ONT online duration'),
            'ONT distance(m)': info.get('ONT distance(m)'),
            'ONT-ID': info.get('ONT-ID'),
            'SN': info.get('SN'),
            'Temperature': info.get('Temperature'),
            'Run state': info.get('Run state')
        }
        return simple_info
    except Exception as e:
        return {"error": str(e)}


def onu_optical_info(gpon, slot, port, iid):
    """
    Получить оптическую информацию об ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"display ont optical-info {port} {iid}\n",
        " "
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}
    try:
        return info_parser(normalize(data))
    except Exception as e:
        return {"error": str(e)}


def onu_optical_info_simple(gpon, slot, port, iid):
    """
    Получить урезанную оптическую информацию об ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"display ont optical-info {port} {iid}\n",
        " "
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}
    try:
        info = info_parser(normalize(data))
        simple_info = {
            'Rx optical power(dBm)': info.get('Rx optical power(dBm)'),
            'Tx optical power(dBm)': info.get('Tx optical power(dBm)'),
            'OLT Rx ONT optical power(dBm)': info.get('OLT Rx ONT optical power(dBm)'),
        }
        return simple_info
    except Exception as e:
        return {"error": str(e)}


def next_free_index(gpon):
    """
    Получить свободный service-port
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        "display service-port next-free-index\n"
    ]

    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}
    try:
        for line in data.split("\n"):
            if "Next valid free service" in line:
                key, val = line.split(":", 1)
                return {key.strip(): val.strip()}
    except Exception as e:
        return {"error": str(e)}


def service_port_list(gpon):
    """
    Получить список всех service-ports
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        "display service-port all\n",
        "\n",
        "  "*30
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=10)
    if error:
        return {"error": error}
    lst = []
    try:
        for i in normalize(data, striped=False):
            if i[:9].strip().isdigit():
                vlan = i[9:14].strip()
                slot = i[28:31].strip()
                port = i[33:35].strip()
                iid = i[36:40].strip()
                state = i[74:].strip()
                srv_port = i[:9].strip()
                lst.append(
                    {"service_port": srv_port, "onu_id": iid, "state": state, "port": port, "slot": slot, "vlan": vlan}
                )
        return lst
    except Exception as e:
        return {"error": str(e)}


def auto_find(gpon, slot, port):
    """
    Получить список незарегистрированных ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"display ont autofind {port}\n",
        "  " * 10
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}
    lst = []
    lines_lst = {}
    f = False
    try:
        for line in normalize(data):
            if "-"*10 in line:
                lines_lst["port"] = port
                lines_lst["slot"] = slot
                lines_lst["gpon"] = gpon
                lst.append(lines_lst)
                lines_lst = {}
                f = True
                continue
            if f:
                ln = line.split(':', 1)
                if not ln[0]:
                    break
                lines_lst[ln[0].strip()] = ln[1].strip()
        return lst[1:]
    except Exception as e:
        return {"error": str(e)}


def optical_ping(gpon, slot, port, onu_id):
    """
    Оптический пинг ONT
    """

    try:
        res = onu_optical_info(gpon, slot, port, onu_id)["Rx optical power(dBm)"]
    except KeyError:
        res = "offline"
    return res


def register_onu(gpon, slot, port, name, sn, srv_profile, line_profile):
    """
    Зарегистрировать ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"""ont confirm {port} sn-auth {sn} omci ont-lineprofile-id {line_profile} ont-srvprofile-id {srv_profile} desc "{name}"\n"""
        "\n\n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)

    if "Failure" in data:
        return failure_parser(normalize(data))
    elif error:
        return {"error", error}
    else:
        lines = normalize(data)
        for line in lines:
            if "PortID" in line:
                onu_id = line.split(',')[1].split(':')[1].strip()
                return {"success": "ONT Registered", "onu_id": onu_id}


def register_onu_manual(gpon, slot, port, name, sn, srv_profile, line_profile):
    """
    Зарегистрировать ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"""ont add {port} sn-auth {sn} omci ont-lineprofile-id {line_profile} ont-srvprofile-id {srv_profile} desc "{name}"\n"""
        "\n\n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)

    if "Failure" in data:
        return failure_parser(normalize(data))
    elif error:
        return {"error", error}
    else:
        lines = normalize(data)
        for line in lines:
            if "PortID" in line:
                onu_id = line.split(',')[1].split(':')[1].strip()
                return {"success": "ONT Registered", "onu_id": onu_id}


def delete_onu(gpon, slot, port, onu_id):
    """
    Удалить зарегистрированную ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"ont delete {port} {onu_id}\n"
        "\n\n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)

    if "Failure" in data:
        return failure_parser(normalize(data))
    elif error:
        return {"error", error}
    else:
        return {"success": "ONT Deleted"}


def add_srv_port(gpon, slot, port, onu_id, service_port, vlan, gem):
    """
    Зарегистрировать service-port
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"service-port {service_port} vlan {vlan} gpon {slot}/{port} ont {onu_id} gemport {gem} multi-service user-vlan {vlan} tag-transform translate\n",
        "\n\n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)

    if "Failure" in data:
        return failure_parser(normalize(data))
    elif error:
        return {"error", error}
    elif "Command:" in data:
        return {"success": "Service-port registered"}
    else:
        return {"error": "Unknown 0x01"}


def undo_srv_port(gpon, service_port):
    """
    Удалить service-port
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"undo service-port {service_port}\n",
        "\n\n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if "Failure" in data:
        return failure_parser(normalize(data))
    elif error:
        return {"error", error}
    else:
        return {"success": "Service-port deleted"}


def native_vlan(gpon, slot, port, onu_id, vlan):
    """
    Прописать Native-vlan на ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n"
        f"ont port native-vlan {port} {onu_id} eth 1 vlan {vlan} priority 0\n",
        "\n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}
    fail = failure_parser(normalize(data))
    if fail:
        return fail
    return {"success": "Native-vlan registered."}


def traffic_vlan(gpon, vlan):
    """
    Получить траффик в VLAN
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"display traffic vlan {vlan}\n",
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}
    try:
        lst = [i for i in normalize(data)[-4].split(' ') if i]
        up = int(lst[1]) / 1024
        down = int(lst[2]) / 1024
        return {"up": up, "down": down}
    except Exception as e:
        return {"error": str(e)}


def traffic_port(gpon, slot, port):
    """
    Получить траффик на GPON-порту
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"int gpon {slot}\n",
        f"display port traffic {port}\n",
    ]
    data, error = conn.exec(cmds=cmds, end_term="Down traffic", timeout=10)
    if error:
        return {"error": error}
    try:
        up, down = normalize(data)[-2:]
        up = int(up.split(':')[1].strip()) / 1024
        down = int(down.split(':')[1].strip()) / 1024
        return {"up": up, "down": down}
    except Exception as e:
        return {"error": str(e)}


def mac_service_port(gpon, service_port):
    """
    Получить MAC-адрес по service-port
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"display mac-address service-port {service_port}\n",
        " \n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}

    mac_lst = []
    try:
        for line in normalize(data):
            k = re.search(r"([0-9A-Fa-f]{4}-){2}([0-9A-Fa-f]{4})", line)
            if k:
                res = k.group().upper().replace('-', '')
                mac_lst.append("-".join([res[i:i + 2] for i in range(0, len(res), 2)]))
    except Exception as e:
        return {"error": str(e)}
    return mac_lst


def mac_onu_port(gpon, slot, port, onu_id) -> list | dict:
    """
    Получить MAC-адрес по ID-ONT
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"display mac-address port {slot}/{port} ont {onu_id}\n",
        "       \n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x321", timeout=5)
    if error:
        return {"error": error}

    mac_lst = []
    try:
        for line in normalize(data):
            k = re.search(r"([0-9A-Fa-f]{4}-){2}([0-9A-Fa-f]{4})", line)
            if k:
                res = k.group().upper().replace('-', '')
                mac_lst.append("-".join([res[i:i+2] for i in range(0, len(res), 2)]))
    except Exception as e:
        return {"error": str(e)}
    return mac_lst


def profile(gpon, type_profile):
    """
    Получить список line или srv профилей
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"display ont-{type_profile}profile gpon all\n",
        "   \n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="x3211", timeout=5)
    if error:
        return {"error": error}
    lines = normalize(data, del_separators=True, striped=False)
    lst = []
    for line in lines:
        profile_id = line[:7].strip()
        profile_name = line[10:55].strip()
        binding_times = line[56:].strip()
        if profile_id.isdigit():
            lst.append({"id": profile_id, "name": profile_name, "bind": binding_times})
    return lst


def save_config(gpon):
    """
    Сохранить конфигурацию
    """

    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        "conf\n",
        f"save\n",
        "\n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="Configuration file has been saved", timeout=10)
    if error:
        return {"error": error}
    return {"success": "Config saved."}


def save_config_thread():
    gar = Thread(daemon=True, target=save_config, args=('garage',))
    et = Thread(daemon=True, target=save_config, args=('etag',))
    gar.start()
    et.start()
    gar.join()
    et.join()


def mac_all(gpon):
    """
    Получить полный список MAC
    """
    conn = gpon_connection(gpon)
    cmds = [
        "en\n",
        f"display mac-address all\n",
        "\n\n",
        " "*200,
        "\n\n"
    ]
    data, error = conn.exec(cmds=cmds, end_term="Total: ", timeout=30)
    if error:
        return {"error": error}

    mac_lst = []
    try:
        for i in normalize(data, striped=False):
            count = 0
            k = re.search(r"([0-9A-Fa-f]{4}-){2}([0-9A-Fa-f]{4})", i)
            if k:
                srv = i[:9].strip()
                if srv.isdigit():
                    raw_mac = i[20:35].strip().upper().replace('-', '')
                    mac = "-".join([raw_mac[i:i + 2] for i in range(0, len(raw_mac), 2)])
                    slot = i[45:50].replace(" ", "")
                    port = i[51:53].strip()
                    iid = i[55:58].strip()
                    vlan = i[-5:].strip()
                    count += 1
                    mac_lst.append(
                        {
                            "srv": srv,
                            "mac": mac,
                            "slot": slot,
                            "port": port,
                            "ont_id": iid,
                            "vlan": vlan
                        }
                    )
    except Exception as e:
        return {"error": str(e)}
    return mac_lst

