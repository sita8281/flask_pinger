from app import db, login_manager
from flask_login import UserMixin
import pickle


@login_manager.user_loader
def load_user(user_id):
    usr = db.session.query(User).get(user_id)
    # usr.last_visit = datetime.now()
    # db.session.add(usr)
    # db.session.commit()
    return usr


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(30), unique=True)
    passw = db.Column(db.String(30))
    privilege = db.Column(db.String(20))
    carbon_login = db.Column(db.String(30))
    carbon_passw = db.Column(db.String(30))
    user_data = db.Column(db.Text)  # json text
    last_visit = db.Column(db.DateTime)


class HostFolder(db.Model):
    __tablename__ = 'host_folders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    hosts = db.relationship('Host', backref='host_folders')


class Host(db.Model):
    __tablename__ = 'hosts'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    folder_id = db.Column(db.Integer, db.ForeignKey('host_folders.id'))  # связь с таблицей HostFolder
    state = db.Column(db.String(20))
    change_state = db.Column(db.String(50))
    checking = db.Column(db.Integer)


class IcmpParams(db.Model):
    __tablename__ = 'icmp_params'
    id = db.Column(db.Integer, primary_key=True)
    ping_interval = db.Column(db.Integer)  # задержка между глобальными проверками
    icmp_count = db.Column(db.Integer)  # кол-во icmp пакетов на хост
    icmp_interval = db.Column(db.Integer)  # задержка между icmp пакета на хост
    ping_workers = db.Column(db.Integer)  # кол-во рабочих потоков, влияет на скорость проверки
    icmp_timeout = db.Column(db.Integer)  # таймаут icmp пакета


class GponProfiles(db.Model):
    __tablename__ = 'gpon_profiles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # название профиля
    vlan = db.Column(db.Integer)  # привязанный vlan
    gemport = db.Column(db.Integer)  # Gem порт
    srv_profile = db.Column(db.Integer)
    line_profile = db.Column(db.Integer)


class GponParams(db.Model):
    __tablename__ = 'gpon_params'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # название gpon блока
    tag = db.Column(db.String(20))  # тег gpon блока
    ip = db.Column(db.String(20))  # ip gpon блока
    port = db.Column(db.Integer)  # port
    login = db.Column(db.String(50))
    passw = db.Column(db.String(50))


class NasApiParams(db.Model):
    __tablename__ = 'nas_api_params'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ip = db.Column(db.String(20))
    port = db.Column(db.Integer)
    login = db.Column(db.String(50))
    passw = db.Column(db.String(50))


class CarbonApiParams(db.Model):
    __tablename__ = 'carbon_api_params'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ip = db.Column(db.String(20))
    port = db.Column(db.Integer)


class CarbonApiData(db.Model):
    __tablename__ = 'carbon_api_data'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    date = db.Column(db.String(20))
    data = db.Column(db.PickleType)


class NasDumps(db.Model):
    __tablename__ = 'nas_dumps'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Integer)
    dump = db.Column(db.PickleType)


class SwDumps(db.Model):
    __tablename__ = 'sw_dumps'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Integer)
    dump = db.Column(db.PickleType)


class ForwardGatewayParams(db.Model):
    __tablename__ = 'forward_gateway_params'
    id = db.Column(db.Integer, primary_key=True)
    external_ip = db.Column(db.String(20))
    external_port = db.Column(db.Integer)


class ConfigStorage(db.Model):
    __tablename__ = 'config_storage'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    date = db.Column(db.String(20))
    text = db.Column(db.Text)


class ConnectStatements(db.Model):
    __tablename__ = 'connect_statements'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(30))
    name = db.Column(db.String(200))
    for_whom = db.Column(db.String(100))
    for_whom_color = db.Column(db.String(40))
    status = db.Column(db.Integer)
    messages = db.Column(db.LargeBinary)
    folder_id = db.Column(db.Integer)

    @property
    def to_serializeble(self) -> dict:
        return dict(
            id=self.id,
            date=self.date,
            name=self.name,
            for_whom=self.for_whom,
            for_whom_color=self.for_whom_color,
            status=self.status,
            folder_id=self.folder_id
        )

    @property
    def lst(self) -> list:
        return [self.date, self.name, self.for_whom, self.status, self.messages, self.for_whom_color, self.folder_id]

    @lst.setter
    def lst(self, new_list):
        self.date, self.name, self.for_whom, self.status, self.messages, self.for_whom_color, self.folder_id = new_list


class StatementsFolder(db.Model):
    __tablename__ = 'statement_folder'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
