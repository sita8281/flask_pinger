import paramiko
import re
import logging


logger = logging.getLogger('nas_daemon')


class NasAPI:
    """Реализация простого API для опроса Access-сервера"""

    def __init__(self, ip: str, port: int, login: str, passw: str, name: str = 'noname'):
        self.ip = ip
        self.port = port
        self.login = login
        self.passw = passw
        self.name = name
        self._connection = None

    def __del__(self):
        if self._connection:
            self._connection.close()

    def _connect_server(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self.ip,
                username=self.login,
                password=self.passw,
                port=self.port,
                allow_agent=False,
                look_for_keys=False,
                timeout=1
            )
        except Exception as e:
            logger.error(f'Ошибка при попытке соединения с сервером <{self.ip}:{self.port}>')
            return
        self._connection = client

    @staticmethod
    def _processing_str(string):
        """Метод возвращает обработанную строку
        он убирает двойные кавычки и оставлает то,
        что было в их пределах"""
        processed_s = ''
        flag = True
        for i in string:
            if i == '"':
                if not flag:
                    flag = True
                    break
                flag = False
            else:
                processed_s += i
        return processed_s

    def _parsing_data(self, data: str) -> dict:
        """Метод парсинга MAC адресов и логинов из строки
        возвращает dict: {логин: mac,}"""
        dict_logins_and_mac = {}
        splited_strings = data.split('\n')
        for string in splited_strings:
            login = re.search(r'(?<=name=)\".{20}', string)
            mac = re.search(r'([\dA-Fa-f]{2}[:-]){5}([\dA-Fa-f]{2})', string)
            if login and mac:
                dict_logins_and_mac[self._processing_str(login.group())] = mac.group().replace(':', '-', 5)
        return dict_logins_and_mac

    def _execute(self, command: str) -> dict | None:

        if not self._connection:
            self._connect_server()

        if self._connection:
            try:
                stdin, stdout, stderr = self._connection.exec_command(command, timeout=1)
                data = self._parsing_data(stdout.read().decode('ascii'))
                return data
            except paramiko.SSHException as e:
                self._connection.close()
                self._connection = None
                # logger.error(f'Ошибка paramiko при попытке выполнения команды: {command}')
                # logger.exception(e)
            except Exception as e:
                pass
                # logger.error(f'Необработанная ошибка при попытке выполнения команды: {command}')
                # logger.exception(e)
        return

    def get_pppoe_sessions(self) -> dict:
        sessions = self._execute(command='/ppp active print detail')

        if not sessions:
            logger.error(f'Сервер {self.name} не доступен, сессии не получены')
            return {'error': f'{self.name} is not available'}
        return {'sessions': sessions}
