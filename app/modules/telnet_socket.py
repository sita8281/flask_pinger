import socket
import time


class TelnetGponExec(socket.socket):
    def __init__(self, login, password, host):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)

        self.login = login
        self.password = password
        self.host = host

        self.buffer = b""
        self.settimeout(2)   # timeout authenticate

    def __del__(self):
        try:
            self.shutdown(0)
            self.close()
        except OSError:
            pass

    def _auth(self):
        self.connect(self.host)
        self.recv_to("User name:")
        self.sendall(f"{self.login}\n{self.password}\n".encode("ascii"))
        self.recv_to("MA5608T>")
        self.clear()

    def clear(self):
        self.buffer = b""

    def recv_to(self, end_term=""):
        end_term = end_term.encode("ascii")
        while True:
            data = self.recv(8192)
            if not data:
                break
            self.buffer += data
            if end_term in self.buffer[-100:]:
                return self.buffer

    def exec(self, cmds: [list, tuple], end_term: [str], sleep=0, timeout=3) -> tuple:
        error = None
        try:
            try:
                self._auth()
            except socket.timeout:
                return '', "auth"
            for cmd in cmds:
                self.sendall(cmd.encode("ascii"))
            if sleep != 0:
                time.sleep(sleep)

            self.settimeout(timeout)
            self.sendall(end_term.encode("ascii"))
            self.recv_to(end_term)

        except socket.timeout:
            error = "timeout"
        except OSError:
            error = "socket"

        return self.buffer.decode("ascii"), error

    def conn(self):
        self._auth()





