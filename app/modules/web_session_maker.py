from threading import Thread
import time
import uuid


class SessionMaker(Thread):
    _online_users = {}
    daemon = True
    timeout_session = 300

    def run(self) -> None:
        print(' * Web Sessions Daemon: on')
        while True:
            time.sleep(2)
            try:
                for key, val in self._online_users.items():
                    if time.time() - val[1] > self.timeout_session:
                        self._disconnect(key)
            except Exception:
                pass

    def connect(self, session_token: str, remote_ip: str, login: str) -> str | None:
        if self._online_users.get(session_token):
            self._online_users[session_token][0] = remote_ip
            self._online_users[session_token][1] = int(time.time())
            return self._online_users[session_token][2]

        else:
            self._online_users[session_token] = [remote_ip, int(time.time()), None, str(uuid.uuid4()), login]

    def _disconnect(self, session_token: str) -> None:
        if session_token in self._online_users:
            del self._online_users[session_token]

    def logout_signal(self, session_id) -> None:
        for key, val in self._online_users.items():
            if val[3] == session_id:
                self._online_users[key][2] = 'logout'

    @property
    def get_connections(self) -> list[dict]:
        return [
            {'address': usr[0], 'status': usr[2], 'id': usr[3], 'login': usr[4]} for key, usr in self._online_users.items()
        ]



