# -*- coding: utf-8 -*-

import signal
import os
# linux 默认就是epoll
from twisted.internet import reactor
import setproctitle

from ..log import logger
from client_connection import ClientConnectionFactory
from worker_connection import WorkerConnectionFactory
from admin_connection import AdminConnectionFactory
from task_dispatcher import TaskDispatcher
from stat_counter import StatCounter
from .. import constants


class Proxy(object):
    """
    proxy相关
    """

    type = constants.PROC_TYPE_PROXY

    client_connection_factory_class = ClientConnectionFactory
    worker_connection_factory_class = WorkerConnectionFactory
    admin_connection_factory_class = AdminConnectionFactory

    app = None

    host = None
    port = None

    # 任务调度器
    task_dispatcher = None
    # 统计
    stat_counter = None

    def __init__(self, app, host, port):
        """
        构造函数
        :return:
        """
        self.app = app
        self.host = host
        self.port = port

        self.task_dispatcher = TaskDispatcher()
        self.stat_counter = StatCounter(self.app.tasks_time_benchmark)

    def run(self):
        setproctitle.setproctitle(self.app.make_proc_name(self.type))

        # 主进程
        self._handle_proc_signals()

        ipc_directory = os.path.dirname(self.app.ipc_address_tpl)
        if not os.path.exists(ipc_directory):
            os.makedirs(ipc_directory)

        # 启动监听worker
        for group_id in self.app.group_conf:
            ipc_address = self.app.ipc_address_tpl % group_id

            # 防止之前异常导致遗留
            if os.path.exists(ipc_address):
                os.remove(ipc_address)

            # 给内部worker通信用的
            reactor.listenUNIX(ipc_address, self.worker_connection_factory_class(self, group_id))

        # 启动对外监听
        reactor.listenTCP(self.port, self.client_connection_factory_class(self),
                          backlog=self.app.proxy_backlog, interface=self.host)

        # 启动admin服务
        if self.app.admin_address:
            reactor.listenTCP(self.app.admin_address[1], self.admin_connection_factory_class(self),
                              interface=self.app.admin_address[0])

        try:
            reactor.run(installSignalHandlers=False)
        except KeyboardInterrupt:
            pass
        except:
            logger.error('exc occur.', exc_info=True)

    def _handle_proc_signals(self):
        def exit_handler(signum, frame):
            """
            在centos6下，callFromThread(stop)无效，因为处理不够及时
            """
            try:
                reactor.stop()
            except:
                pass

        # 强制结束，抛出异常终止程序进行
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        # 直接停止
        signal.signal(signal.SIGTERM, exit_handler)
        # 忽略，因为这个时候是在重启worker
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
