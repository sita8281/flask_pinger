import os


basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')


class BaseConfig:
    SECRET_KEY = "SUPER_SECRET_KET :)"
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'main_db.sqlite3')


class DevelopementConfig(BaseConfig):
    DEBUG = True
    ICMP_DAEMON = False
    NAS_DAEMON = False
    FORWARD_GATEWAY_DAEMON = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    ICMP_DAEMON = True
    NAS_DAEMON = True
    FORWARD_GATEWAY_DAEMON = True


class DisableIcmpConfig(BaseConfig):
    DEBUG = True
    ICMP_DAEMON = False
    NAS_DAEMON = True
    FORWARD_GATEWAY_DAEMON = True
