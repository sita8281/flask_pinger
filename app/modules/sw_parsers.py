import re


def parser(data):
    ports = {}
    for i in data.split('\n'):
        try:
            mac = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2}....)', i).group()
            mac, port = mac.strip().replace('  ', ' ').split(' ')
            ports[mac] = port
        except AttributeError:
            pass
    return ports


def zyxel(data):
    ports = {}
    for i in data.split('\n'):
        k = i.strip()
        try:
            mac = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', k).group()
            ports[mac.upper().replace(':', '-')] = k[:2].strip()
        except AttributeError:
            pass
    return ports


def cisco(data):
    ports = {}
    for i in data.split('\n'):
        try:
            mac = re.search(r'([0-9a-f]{4}[.]){2}([0-9A-Fa-f]{4})', i).group()
            mac = mac.upper().replace('.', '')
            reconstruct_mac = '-'.join([mac[i:i+2] for i in range(0, len(mac), 2)])
            if len(i) > 60:
                port = i[72:].strip()
            else:
                port = i[38:].strip()
            ports[reconstruct_mac] = port
        except AttributeError:
            pass
    return ports


def orion(data):
    ports = {}
    for i in data.split('\n'):
        try:
            mac = re.search(r'([0-9A-F]{4}[.]){2}([0-9A-Fa-f]{4})', i).group()
            mac = mac.upper().replace('.', '')
            reconstruct_mac = '-'.join([mac[i:i + 2] for i in range(0, len(mac), 2)])
            if len(i) > 50:
                port = i[55:58].strip()
            else:
                port = i[18:21].strip()
            ports[reconstruct_mac] = port

        except AttributeError:
            pass
    return ports
