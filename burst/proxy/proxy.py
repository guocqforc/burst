# -*- coding: utf-8 -*-

import signal
# linux 默认就是epoll
from twisted.internet import reactor

from ..log import logger
from . import ClientConnectionFactory, WorkerConnectionFactory
from burst.proxy.task_dispatcher import TaskDispatcher


class Proxy(object):
    """
    proxy相关
    """

    app = None

    client_connection_factory_class = ClientConnectionFactory
    worker_connection_factory_class = WorkerConnectionFactory

    host = None
    port = None

    # 任务调度器
    task_dispatcher = TaskDispatcher()

    def __init__(self, app):
        """
        构造函数
        :return:
        """
        self.app = app

    def run(self, host=None, port=None):
        self.host = host
        self.port = port

        # 主进程
        self._handle_proc_signals()

        reactor.listenTCP(port, self.client_connection_factory_class(self),
                          backlog=self.app.backlog, interface=host)

        # 启动监听worker
        for group_id in self.app.group_conf:
            address = self.app.worker_address_tpl % group_id

            # 给内部worker通信用的
            reactor.listenUnix(address, self.worker_connection_factory_class(self, group_id))

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
