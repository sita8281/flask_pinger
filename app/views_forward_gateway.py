from app import app
from .modules import vpn_gateway
from flask import redirect, request
from flask_login import login_required, current_user
import logging

logger = logging.getLogger('vpn')


@app.route('/forward_gateway/', methods=['GET'])
@login_required
def forward_gateway_open():
    ip = request.args.get('ip')
    port = request.args.get('port')
    if ip and port.isdigit():
        vpn_gateway.run_vpn(ip=ip, port=int(port))
    response_redirect = redirect(location=f'http://{vpn_gateway.get_ip}:{vpn_gateway.get_port}/')
    response_redirect.set_cookie(key='session', value='', expires=0)
    logger.info(f'{current_user.login}: открыл VPN -> {ip}:{port}')
    return response_redirect
