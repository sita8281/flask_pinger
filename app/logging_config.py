import logging


def init_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('file.log', encoding='utf-8')
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(name)s] [%(levelname)s]  %(message)s', datefmt='%Y/%m/%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


init_logger('app')
init_logger('pinger')
init_logger('carbon')
init_logger('gpon')
init_logger('helpdesk')
init_logger('admin_panel')
init_logger('vpn')
init_logger('nas_daemon')
init_logger('search_port')
init_logger('pinger_daemon')
init_logger('vpn_daemon')
init_logger('config_storage')
init_logger('connect_statements')


