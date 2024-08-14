from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from . import logging_config
import logging


frontend_version = '11'
app = Flask(__name__)
app.config.from_object('config.ProductionConfig')
# app.config.from_object('config.DevelopementConfig')
# app.config.from_object('config.DisableIcmpConfig')

logging.getLogger('app').info('Приложение запущено и ожидает новых подключений')
db = SQLAlchemy(app)  # SqlAlchemy получает путь в БД из конфига flask.app
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # если 401, redirect на login страницу


# прокидка версии фронта в jinja2 renderer
@app.context_processor
def front_ver():
    return {'static_ver': f'?ver={frontend_version}'}

from . import (
    views,
    models,
    views_cfg_storage,
    views_permission,
    views_pinger,
    views_gpon,
    views_search_port,
    views_forward_gateway,
    views_carbon,
    deil_api_context,
    views_helpdesk,
    views_connect_statements,
    views_online_users
)
from .modules import pinger
