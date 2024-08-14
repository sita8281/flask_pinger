import gc
import queue
from threading import Thread
from queue import Queue
import icmplib
from app import app, models, db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging


logger = logging.getLogger('pinger_daemon')


class PINGworker(Thread):
    def __init__(self, iid, ip, name, state, change_state, count, interval, timeout):
        super().__init__(daemon=True)
        self._id = iid
        self._ip = ip
        self._name = name
        self._time_change = change_state
        self._state = state  # offline, online, error, '', pause
        self._count = count
        self._interval = interval
        self._timeout = timeout

    def run(self) -> None:

        if self._state == 'pause':
            return

        try:
            result = icmplib.ping(self._ip, self._count, self._interval, self._timeout)
        except Exception as e:
            logger.error(f'При попытке запустить пинг хоста <{self._ip}>, возникла ошибка')
            logger.exception(e)
            if self._state == 'error':
                return
            self._time_change = datetime.now().strftime('%Y/%m/%d %H:%M')
            self._state = 'offline'
            return

        if result.is_alive:
            # print(self._ip, 'ONLINE')
            if self._state != 'online':
                self._state = 'online'
                self._time_change = datetime.now().strftime('%Y/%m/%d %H:%M')
                logger.warning(f'Хост <{self._ip}> {self._name} [включился]')
        else:
            # print(self._ip, 'OFFLINE')
            if self._state == 'online':
                self._state = 'offline'
                self._time_change = datetime.now().strftime('%Y/%m/%d %H:%M')
                logger.warning(f'Хост <{self._ip}> {self._name} [отключился]')

    @property
    def state(self):
        return self._state

    @property
    def change_state(self):
        return self._time_change

    @property
    def iid(self):
        return self._id


class ICMPdaemon(Thread):
    """
    Поток-демон, выполняет одну из основных функций данного приложени
    Его работа сопряжена с БД, он берёт из неё список хостов
    Далее каждый хост проверяется на доступность ICMP
    Работает поток всегда
    """

    def __init__(self):
        super().__init__(daemon=True)

        self._timer = 0
        self._latch = True  # защёлка, не позволяет запускать новую проверку, пока не завершиться старая
        self._queue_signal = Queue(maxsize=1)

    def _init_icmp(self):
        # получаем контекст flask, для корректной работы с БД из другого потока
        with app.app_context():
            params = db.session.query(models.IcmpParams).get(1)
            self._PING_INTERVAL = params.ping_interval
            self._PING_WORKERS = params.ping_workers
            self._ICMP_COUNT = params.icmp_count
            self._ICMP_INTERVAL = params.icmp_interval
            self._ICMP_TIMEOUT = params.icmp_timeout
            self._all_hosts = db.session.query(models.Host).all()

    def run(self) -> None:
        if app.config.get('ICMP_DAEMON'):
            print(' * Icmp Daemon: on')
        else:
            print(' * Icmp Daemon: off')
            return

        self._init_icmp()
        self._PING_INTERVAL = 1  # при запуске потока, проверка начнётся чреез 1 сек

        while True:
            try:
                obj = self._queue_signal.get(block=True, timeout=self._PING_INTERVAL)
                self._init_icmp()
                hosts = self._all_hosts
                if obj.get('SIGNAL') == 'PING_DEAD':
                    hosts = list(filter(lambda x: x.state == 'offline', hosts))
                elif obj.get('SIGNAL') == 'PING_ONE':
                    hosts = list(filter(lambda x: x.id == obj.get('ID'), hosts))
            except queue.Empty:
                self._init_icmp()
                hosts = self._all_hosts
            hosts = list(filter(lambda x: x.state != 'pause', hosts))
            self._latch = True
            try:
                self._run_all_checking(hosts)
            except Exception as e:
                logger.error('При попытке запуска проверки всех хостов, возникла ошибка')
                logger.exception(e)
            self._latch = False

    def _run_all_checking(self, hosts):

        pool = []
        for c, host in enumerate(hosts):
            pool.append(host)
            if c % self._PING_WORKERS == 0:
                self._icmp_check_pool(pool)
                pool = []
        else:
            self._icmp_check_pool(pool)

    def _icmp_check_pool(self, pool):
        thread_pool = []

        with app.app_context():
            for hst in pool:
                thread_pool.append(
                    PINGworker(
                        hst.id,
                        hst.ip,
                        hst.name,
                        hst.state,
                        hst.change_state,
                        self._ICMP_COUNT,
                        self._ICMP_INTERVAL,
                        self._ICMP_TIMEOUT
                    )
                )
                try:
                    host = db.session.query(models.Host).get(hst.id)
                    if host:
                        host.checking = 1
                        db.session.flush()
                        db.session.commit()
                except SQLAlchemyError as e:
                    logger.error('При установке флага проверки хоста, в базе данных возникла ошибка')
                    logger.exception(e)
                    db.session.rollback()

        for thr in thread_pool:
            thr.start()
        for thr in thread_pool:
            thr.join()

        with app.app_context():
            for final_thread in thread_pool:
                host = db.session.query(models.Host).get(final_thread.iid)
                if not host:
                    continue
                host.checking = 0
                host.state = final_thread.state
                host.change_state = final_thread.change_state
                try:
                    db.session.flush()
                    db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    logger.error('При снятии флага проверки хоста, в базе данных возникла ошибка')
                    logger.exception(e)
                del final_thread
        gc.collect()

    def _run_checking(self, queue_message):
        if not self._latch:
            try:
                self._queue_signal.put_nowait(queue_message)
            except queue.Full:
                return 'Очередь ожидания переполнена, попробуйте позже'
            return 'Проверка хостов запущена'
        else:
            return 'Проверка хостов уже запущена, дождитесь завершения'

    def ping_dead(self):
        return self._run_checking(queue_message={'SIGNAL': 'PING_DEAD'})

    def ping_one(self, host_id):
        return self._run_checking(queue_message={'SIGNAL': 'PING_ONE', 'ID': host_id})

    def ping_all(self):
        return self._run_checking(queue_message={'SIGNAL': 'PING_ALL'})
