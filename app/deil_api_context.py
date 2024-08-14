from app import app, db, models
from .modules.deil_api import DeilAPI
from flask_login import current_user
from flask import abort
from cryptography.fernet import Fernet


def decrypt_password(password):
    cr = Fernet(key=app.config.get('DEIL_API_CRYPTO'))
    return cr.decrypt(password).decode('utf-8')


class DeilContext:
    deil_api = None

    def __enter__(self):
        login = current_user.carbon_login
        passw = current_user.carbon_passw
        if not login or not passw:
            return abort(401)
        params = db.session.query(models.CarbonApiParams).get(1)
        self.deil_api = DeilAPI(login=login, passw=decrypt_password(passw), ip=params.ip, port=params.port)
        self.deil_api.authenticate()
        return self.deil_api

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass