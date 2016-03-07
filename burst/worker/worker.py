# -*- coding: utf-8 -*-

import signal
import setproctitle
import os

from .connection import Connection
from ..share.log import logger
from .request import Request
from ..share import constants


class Worker(object):

    type = constants.PROC_TYPE_WORKER

    request_class = Request
    connection_class = Connection
    got_first_request = False

    group_id = None

    # 是否有效(父进程中代表程序有效，子进程中代表worker是否有效)
    enable = True

    def __init__(self, app, group_id):
        """
        构造函数
        :return:
        """
        self.app = app
        self.group_id = group_id

    def run(self):
        setproctitle.setproctitle(self.app.make_proc_name(
            '%s:%s' % (self.type, self.group_id)
        ))

        self._handle_proc_signals()
        self._on_worker_run()

        try:
            address = os.path.join(
                self.app.config['IPC_ADDRESS_DIRECTORY'],
                self.app.config['WORKER_ADDRESS_TPL'] % self.group_id
            )
            conn = self.connection_class(self, address, self.app.config['WORKER_CONN_TIMEOUT'])
            conn.run()
        except KeyboardInterrupt:
            pass
        except:
            logger.error('exc occur.', exc_info=True)

    def _on_worker_run(self):
        self.app.events.create_worker(self)
        for bp in self.app.blueprints:
            bp.events.create_app_worker(self)

    def _handle_proc_signals(self):
        def exit_handler(signum, frame):
            # 防止重复处理KeyboardInterrupt，导致抛出异常
            if self.enable:
                self.enable = False
                raise KeyboardInterrupt

        def safe_stop_handler(signum, frame):
            self.enable = False

        # 强制结束，抛出异常终止程序进行
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        # 安全停止
        signal.signal(signal.SIGTERM, safe_stop_handler)
        signal.signal(signal.SIGHUP, safe_stop_handler)

