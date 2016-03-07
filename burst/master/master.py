# -*- coding: utf-8 -*-

import os
import copy
import json
import sys
import subprocess
import time
import signal
import setproctitle
from netkit.box import Box
from netkit.contrib.tcp_client import TcpClient
import thread

from ..share.log import logger
from ..share.utils import safe_call
from ..share.thread_timer import ThreadTimer
from ..share import constants


class Master(object):
    """
    master相关
    """

    type = constants.PROC_TYPE_MASTER

    app = None

    enable = True

    # 等待重启所有workers的timer
    restart_workers_timer = None

    # proxy进程列表
    proxy_process = None

    # worker进程列表
    worker_processes = None

    def __init__(self, app):
        """
        构造函数
        :return:
        """
        self.app = app
        self.restart_workers_timer = ThreadTimer()

    def run(self):
        setproctitle.setproctitle(self.app.make_proc_name(self.type))

        self._handle_proc_signals()

        self._spawn_proxy()
        self._spawn_workers()

        thread.start_new(self._connect_to_proxy, ())

        self._monitor_child_processes()

    def _connect_to_proxy(self):
        """
        连接到proxy，因为有些命令要发过来
        :return:
        """
        address = os.path.join(
            self.app.config['IPC_ADDRESS_DIRECTORY'],
            self.app.config['MASTER_ADDRESS']
        )
        client = TcpClient(Box, address=address)

        while True:
            try:
                client.connect()
            except KeyboardInterrupt:
                break
            except:
                # 只要连接失败
                logger.error('connect fail. address: %s', address)
                time.sleep(1)
                continue

            # 读取的数据
            box = client.read()
            if not box:
                logger.info('connection closed.')
                continue

            logger.info('box: %s', box)

            safe_call(self._handle_proxy_data, box)

    def _handle_proxy_data(self, box):
        """
        处理从proxy过来的box
        :param box:
        :return:
        """

        if box.cmd == constants.CMD_ADMIN_CHANGE_GROUP:
            jdata = json.loads(box.body)
            group_id = jdata['payload']['group_id']
            count = jdata['payload']['count']

            # 不能设置成个奇怪的值就麻烦了
            assert isinstance(count, int), 'data: %s' % box.body

            if group_id not in self.app.config['GROUP_CONFIG']:
                self.app.config['GROUP_CONFIG'][group_id] = dict(
                    count=count
                )

            else:
                self.app.config['GROUP_CONFIG'][group_id]['count'] = count

            self._restart_workers()

        elif box.cmd == constants.CMD_ADMIN_RELOAD_WORKERS:
            self._reload_workers()
        elif box.cmd == constants.CMD_ADMIN_RESTART_WORKERS:
            self._restart_workers()
        elif box.cmd == constants.CMD_ADMIN_STOP:
            self._safe_stop()

    def _start_child_process(self, proc_env):
        worker_env = copy.deepcopy(os.environ)
        worker_env.update({
            self.app.config['CHILD_PROCESS_ENV_KEY']: json.dumps(proc_env)
        })

        args = [sys.executable] + sys.argv
        inner_p = subprocess.Popen(args, env=worker_env)
        inner_p.proc_env = proc_env
        return inner_p

    def _spawn_proxy(self):
        proc_env = dict(
            type=constants.PROC_TYPE_PROXY
        )
        self.proxy_process = self._start_child_process(proc_env)

    def _spawn_workers(self):
        self.worker_processes = []

        for group_id, group_info in self.app.config['GROUP_CONFIG'].items():
            proc_env = dict(
                type=constants.PROC_TYPE_WORKER,
                group_id=group_id,
            )

            # 进程个数
            for it in xrange(0, group_info['count']):
                p = self._start_child_process(proc_env)
                self.worker_processes.append(p)

    def _monitor_child_processes(self):
        while 1:
            if self.proxy_process and self.proxy_process.poll() is not None:
                proc_env = self.proxy_process.proc_env
                if self.enable:
                    self.proxy_process = self._start_child_process(proc_env)

            for idx, p in enumerate(self.worker_processes):
                if p and p.poll() is not None:
                    # 说明退出了
                    proc_env = p.proc_env
                    self.worker_processes[idx] = None

                    if self.enable and not self.restart_workers_timer.is_set():
                        # 如果还要继续服务
                        p = self._start_child_process(proc_env)
                        self.worker_processes[idx] = p

            if not filter(lambda x: x, self.worker_processes):
                # 没活着的了worker了

                if self.restart_workers_timer.is_set():
                    # 如果是在等待重启，就直接重启了
                    self.restart_workers_timer.clear()
                    self._spawn_workers()
                    continue
                else:
                    break

            # 时间短点，退出的快一些
            time.sleep(0.1)

    def _restart_workers(self):
        """
        安全停止所有workers
        :return:
        """

        for p in self.worker_processes:
            if p:
                p.send_signal(signal.SIGTERM)

        def final_kill_workers():
            """
            如果到时间还没停止，那就只能强制kill了
            """
            for p in self.worker_processes:
                if p:
                    p.send_signal(signal.SIGKILL)

        self.restart_workers_timer.set(self.app.config['STOP_TIMEOUT'], final_kill_workers)

    def _reload_workers(self):
        """
        reload是热更新，停一个，起一个
        :return:
        """
        for p in self.worker_processes:
            if p:
                p.send_signal(signal.SIGHUP)

    def _safe_stop(self):
        """
        安全停止所有子进程，并最终退出
        如果退出失败，要最终kill -9
        :return:
        """
        self.enable = False

        for p in self.worker_processes + [self.proxy_process]:
            if p:
                p.send_signal(signal.SIGTERM)

        if self.app.config['STOP_TIMEOUT'] is not None:
            signal.alarm(self.app.config['STOP_TIMEOUT'])

    def _handle_proc_signals(self):
        def exit_handler(signum, frame):
            self.enable = False

            # 如果是终端直接CTRL-C，子进程自然会在父进程之后收到INT信号，不需要再写代码发送
            # 如果直接kill -INT $parent_pid，子进程不会自动收到INT
            # 所以这里可能会导致重复发送的问题，重复发送会导致一些子进程异常，所以在子进程内部有做重复处理判断。
            for p in self.worker_processes + [self.proxy_process]:
                if p:
                    p.send_signal(signum)

            # https://docs.python.org/2/library/signal.html#signal.alarm
            if self.app.config['STOP_TIMEOUT'] is not None:
                signal.alarm(self.app.config['STOP_TIMEOUT'])

        def final_kill_handler(signum, frame):
            if not self.enable:
                # 只有满足了not enable，才发送term命令
                for p in self.worker_processes + [self.proxy_process]:
                    if p:
                        p.send_signal(signal.SIGKILL)

        def safe_stop_handler(signum, frame):
            """
            等所有子进程结束，父进程也退出
            """
            self._safe_stop()

        def safe_reload_handler(signum, frame):
            """
            让所有子进程重新加载
            """
            self._reload_workers()

        # INT, QUIT为强制结束
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        # TERM为安全结束
        signal.signal(signal.SIGTERM, safe_stop_handler)
        # HUP为热更新
        signal.signal(signal.SIGHUP, safe_reload_handler)
        # 最终判决，KILL掉子进程
        signal.signal(signal.SIGALRM, final_kill_handler)
