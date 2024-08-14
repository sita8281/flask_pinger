import time
from threading import Thread
from app import app, db, models
from .nas_api import NasAPI
from flask import abort
import logging

logger = logging.getLogger('nas_daemon')


class NASdaemon(Thread):
    daemon = True
    _restart_flag = False
    _sessions_storage = {}

    def run(self) -> None:
        if app.config.get('NAS_DAEMON'):
            print(' * Nas Daemon: on')
        else:
            print(' * Nas Daemon: off')
            return
        self._polling()

    def _init_all_nas(self):
        # получаем контекст flask, для корректной работы с БД из другого потока
        with app.app_context():
            nas_list = db.session.query(models.NasApiParams).all()
            for nas_data in nas_list:
                nas_connection = NasAPI(
                    ip=nas_data.ip,
                    port=nas_data.port,
                    name=nas_data.name,
                    login=nas_data.login,
                    passw=nas_data.passw
                )
                self._sessions_storage[nas_data.id] = [nas_connection, {}]

    def _polling(self):
        try:
            self._init_all_nas()
        except Exception as e:
            pass
            # logger.error('При попытке установить соединения с NAS-servers возникла ошибка')
            # logger.exception(e)

        while True:
            try:
                for nas_id, val in self._sessions_storage.items():
                    nas_conn = val[0]  # объект nas api
                    self._sessions_storage[nas_id][1] = nas_conn.get_pppoe_sessions()
            except Exception as e:
                logger.error('При получении PPPoE-сессий возникла ошибка')
                # logger.exception(e)

            time.sleep(2)

            if self._restart_flag:
                self._init_all_nas()
                logger.warning('данные NAS-servers были обновлены из БД, по сигналу RSRT')
                self._restart_flag = False

    def get_sessions(self, nas_id: int) -> dict | None:
        """Не вызывается внутри этого потока"""
        data = self._sessions_storage.get(nas_id)
        if data:
            return data[1]
        abort(404)

    def get_multiple_sessions(self) -> dict:
        new_sessions_dict = {}
        for key, val in self._sessions_storage.items():
            for login, mac in val[1]['sessions'].items():
                new_sessions_dict[login] = mac
        return new_sessions_dict

    def find_session_by_mac(self, mac: str) -> str | None:
        for val in self._sessions_storage.values():
            for login, _mac in val[1]['sessions'].items():
                if mac == _mac:
                    return login

    def find_session_by_login(self, login: str):
        for val in self._sessions_storage.values():
            for _login, mac in val[1]['sessions'].items():
                if login == _login:
                    return mac

    def restart_init(self):
        self._restart_flag = True






