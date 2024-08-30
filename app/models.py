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
