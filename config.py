import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
load_dotenv(dotenv_path=env_path)


class BaseConfig:
    ENV_PATH = env_path
    BASE_DIR = basedir
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'main_db.sqlite3')
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEIL_API_CRYPTO = bytes(os.getenv('DEIL_API_CRYPTO'), encoding='utf8')


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
