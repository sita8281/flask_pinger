from threading import Thread
import socket
import time
import pickle
from datetime import datetime
from . import sw_parsers
from sqlalchemy import exc
from app import app, models, db


table_keys = {
    'cisco': (b'User Access Verification', b'<username>\nenable\n<password>\nshow mac address-table\n' + b' ' * 100),
    'zyxel': (b'User name:', b'<username>\n<password>\nshow mac address-table all\n' + b' ' * 100),
    'dlink': (b'D-Link', b'<username>\n<password>\nshow fdb\n' + b' ' * 100),
    'orion': (b'Login:', b'<username>\n<password>\nshow mac-address-table l2-address\n' + b' ' * 100)
}


class SwPollerData(Thread):
    def __init__(self, host, name):
        super().__init__(daemon=True)
        self.host = host
        self.name = name
        self.buffer = b''
        self.device = 'unknown'
        self.cmd = b''
        self.status = 'success'
        self.ports = {}

    def run(self) -> None:
        try:
            self.connect()
            self.recv_before_timeout()
            self.check_device()
            self.recv_before_timeout()
        except OSError:
            self.status = "error"

        if self.device == "dlink":
            self.ports = sw_parsers.parser(self.buffer.decode("cp1251"))
        elif self.device == "cisco":
            self.ports = sw_parsers.cisco(self.buffer.decode("cp1251"))
        elif self.device == "zyxel":
            self.ports = sw_parsers.zyxel(self.buffer.decode("cp1251"))
        elif self.device == "orion":
            self.ports = sw_parsers.orion(self.buffer.decode("cp1251"))

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(2)
        self.sock.connect((self.host, 23))

    def check_device(self):
        for device, lst in table_keys.items():
            if lst[0] in self.buffer:
                self.device = device
                self.sock.sendall(lst[1])
                return

    def recv_before_timeout(self):
        while True:
            try:
                data_b = self.sock.recv(8192)
                if not data_b:
                    return
                self.buffer += data_b
            except socket.timeout:
                return


class DumperSW:
    def __init__(self):
        self._busy_flag = False

    def run_dump(self) -> bool:
        """Запустить снятие нового DUMP со всех свитчей"""
        if not self._busy_flag:
            self._busy_flag = True
            self._run()
            return True

    def is_busy(self) -> bool:
        """Получить состояние снятия DUMP"""
        return self._busy_flag

    def _run(self):
        with app.app_context():
            hosts = db.session.query(models.Host).all()
        pollers = [SwPollerData(host=host.ip, name=host.name) for host in hosts]

        Thread(target=self._thread_waiter, args=(pollers,)).start()

    def _thread_waiter(self, pollers):
        try:
            for poll in pollers:
                poll.start()
                time.sleep(0.2)

            for poll in pollers:
                poll.join()

            date = datetime.now().strftime('%Y/%m/%d %H:%M')
            blob = pickle.dumps(
                [dict(device=poll.device, host=poll.host, status=poll.status, name=poll.name, ports=poll.ports) for poll in pollers]
            )

            with app.app_context():
                try:
                    db.session.add(models.SwDumps(date=date, dump=blob))
                    db.session.flush()
                    db.session.commit()
                except exc.SQLAlchemyError:
                    db.session.rollback()
        finally:
            self._busy_flag = False
