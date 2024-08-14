import socket
import select
from threading import Thread
from app import db, models, app
import logging


logger = logging.getLogger('vpn_daemon')


class Forward:

    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.forward.settimeout(1)

    def connect(self, host: tuple):

        try:
            self.forward.connect(host)
            self.forward.settimeout(5)
            return self.forward
        except OSError:
            pass


class ForwardGatewayServer(Thread):
    buffer_size = 8192
    forward_gateway = ('172.16.2.254', 51401)

    def __init__(self):
        super().__init__(daemon=True)

        with app.app_context():
            self.params = db.session.query(models.ForwardGatewayParams).get(1)

        self.wait_io_socks = []
        self.channel = {}
        self.sock = None
        self.data = None
        self.dump = b''
        self.disable_flag = False
        self.switch_flag = False
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((self.params.external_ip, self.params.external_port))
            self.server.listen(10)
        except Exception as e:
            print(f' * Forward Gateway Daemon: {e}')
            logger.error(f'Не удалось запустить поток')
            logger.exception(e)

    @property
    def get_ip(self):
        return self.params.external_ip

    @property
    def get_port(self):
        return self.params.external_port

    def run(self) -> None:

        if not app.config.get('FORWARD_GATEWAY_DAEMON') or self.disable_flag:
            print(' * Forward Gateway Daemon: off')
            return
        else:
            print(' * Forward Gateway Daemon: on')
            self.serve_forever()

    def serve_forever(self, timeout=None):
        self.wait_io_socks.append(self.server)

        while True:
            inputs, _, _ = select.select(self.wait_io_socks, [], [], 600)
            if not inputs:
                self.forward_gateway = ('172.16.2.254', 51401)
                self.reset_channels()

            if self.switch_flag:
                self.reset_channels()
                self.switch_flag = False

            for self.sock in inputs:
                if self.sock == self.server:
                    self.on_accept()
                    break

                try:
                    self.data = self.sock.recv(self.buffer_size)
                except OSError:
                    pass
                finally:
                    if not self.data:
                        self.on_close()
                        break
                    else:
                        self.on_recv()

    def reset_channels(self):
        for sock in self.wait_io_socks:
            try:
                if sock == self.server:
                    continue
                sock.close()
            except OSError:
                pass
        self.channel = {}
        self.wait_io_socks = [self.server]
        # print(self.wait_io_socks)

    def on_recv(self):
        data = self.data

        try:
            sock = self.channel[self.sock]
            sock.sendall(data)
        except (OSError, KeyError):
            pass

    def on_close(self):
        try:
            self.wait_io_socks.remove(self.sock)
            self.wait_io_socks.remove(self.channel[self.sock])
        except ValueError:
            return

        out_forward = self.channel[self.sock]
        in_forward = self.channel[out_forward]

        out_forward.close()
        in_forward.close()

        del self.channel[self.sock]
        del self.channel[out_forward]

    def on_accept(self):

        forward = Forward().connect(self.forward_gateway)
        try:
            client, addr = self.server.accept()
        except OSError:
            return

        if forward:
            self.wait_io_socks.append(client)
            self.wait_io_socks.append(forward)
            self.channel[forward] = client
            self.channel[client] = forward
        else:
            client.close()

    def run_vpn(self, ip: str, port: int):
        try:
            self.forward_gateway = (ip, port)
            self.switch_flag = True
            # self.reset_channels()
        except OSError:
            pass
