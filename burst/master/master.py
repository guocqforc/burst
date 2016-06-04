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
from ..share import constants


class Master(object):
    """
    master相关
    """

    type = constants.PROC_TYPE_MASTER

    app = None

    # 是否有效
    enable = True

    # reload状态
    reload_status = constants.RELOAD_STATUS_STOPPED

    # proxy进程列表
    proxy_process = None

    # worker进程列表
    worker_processes = None

    # 准备好worker进程列表，HUP的时候，用来替换现役workers
    ready_worker_processes = None

    def __init__(self, app):
        """
        构造函数
        :return:
        """
        self.app = app

    def run(self):
        setproctitle.setproctitle(self.app.make_proc_name(self.type))

        self._handle_proc_signals()

        self.proxy_process = self._spawn_proxy()

        # 等待proxy启动，为了防止worker在连接的时候一直报connect失败的错误
        if not self._wait_proxy():
            # 有可能ctrl-c终止，这个时候就要直接返回了
            return

        self.worker_processes = self._spawn_workers()

        thread.start_new(self._connect_to_proxy, ())

        self._monitor_child_processes()

    def _wait_proxy(self):
        """
        尝试连接proxy，如果连接成功，说明proxy启动起来了
        :return:
        """
        address = os.path.join(
            self.app.config['IPC_ADDRESS_DIRECTORY'],
            self.app.config['MASTER_ADDRESS']
        )
        client = TcpClient(Box, address=address)

        while self.enable:
            try:
                client.connect()
                # 连接成功后，就关闭连接
                client.close()
                return True
            except KeyboardInterrupt:
                return False
            except:
                time.sleep(0.1)
                continue

        return False

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

        while self.enable:
            try:
                if client.closed():
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

        if box.cmd == constants.CMD_ADMIN_CHANGE:
            jdata = json.loads(box.body)
            if not self.app.change_group_config(jdata['payload']['group_id'], jdata['payload']['count']):
                logger.error('change group config fail. data: %s', box.body)
                return

            self._reload_workers()

        elif box.cmd == constants.CMD_ADMIN_RELOAD:
            self._reload_workers()
        elif box.cmd == constants.CMD_ADMIN_STOP:
            self._stop_by_signal(signal.SIGTERM)
        elif box.cmd == constants.CMD_MASTER_REPLACE_WORKERS:
            # 要替换workers
            self.reload_status = constants.RELOAD_STATUS_WORKERS_DONE

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
        return self._start_child_process(proc_env)

    def _spawn_workers(self):
        worker_processes = []

        for group_id, group_info in self.app.config['GROUP_CONFIG'].items():
            proc_env = dict(
                type=constants.PROC_TYPE_WORKER,
                group_id=group_id,
            )

            # 进程个数
            for it in xrange(0, group_info['count']):
                p = self._start_child_process(proc_env)
                worker_processes.append(p)

        return worker_processes

    def _monitor_child_processes(self):
        while 1:
            if self.proxy_process and self.proxy_process.poll() is not None:
                proc_env = self.proxy_process.proc_env
                if self.enable:
                    self.proxy_process = self._start_child_process(proc_env)

            for idx, p in enumerate(self.worker_processes):

                if self.reload_status != constants.RELOAD_STATUS_STOPPED:
                    # 如果是处于reload中，那么就不要检测worker状态
                    # 否则会导致worker重连，而proxy那边重新分配任务
                    continue

                if p and p.poll() is not None:
                    # 说明退出了
                    proc_env = p.proc_env
                    self.worker_processes[idx] = None

                    if self.enable:
                        # 如果还要继续服务
                        p = self._start_child_process(proc_env)
                        self.worker_processes[idx] = p

            if not filter(lambda x: x, self.worker_processes):
                # 没活着的了worker了
                break

            if self.reload_status == constants.RELOAD_STATUS_WORKERS_DONE:
                # 先停掉所有的worker
                self._safe_stop_workers()
                # 替换workers
                self.worker_processes = self.ready_worker_processes
                self.ready_worker_processes = list()

                # 结束reload
                self.reload_status = constants.RELOAD_STATUS_STOPPED

            # 时间短点，退出的快一些
            time.sleep(0.1)

    def _kill_processes_later(self, processes, timeout):
        """
        等待一段时间后杀死所有进程
        :param processes:
        :param timeout:
        :return:
        """
        def _kill_processes():
            # 等待一段时间
            time.sleep(timeout)

            for p in processes:
                if p and p.poll() is None:
                    # 说明进程还活着
                    p.send_signal(signal.SIGKILL)

        thread.start_new_thread(_kill_processes, ())

    def _reload_workers(self):
        """
        reload是热更新，全部都准备好了之后，再将worker挨个换掉
        :return:
        """
        if self.reload_status != constants.RELOAD_STATUS_STOPPED:
            return False

        # 正在进行reloading
        self.reload_status = constants.RELOAD_STATUS_PREPARING

        # 给proxy发送信号，告知当前处于替换worker的状态
        self.proxy_process.send_signal(signal.SIGHUP)

        # 启动预备役的workers
        self.ready_worker_processes = self._spawn_workers()

        return True

    def _safe_stop_workers(self):
        """
        停止所有的workers
        :return:
        """

        processes = self.worker_processes[:]

        for p in processes:
            if p:
                p.send_signal(signal.SIGTERM)

        if self.app.config['STOP_TIMEOUT'] is not None:
            self._kill_processes_later(processes, self.app.config['STOP_TIMEOUT'])

    def _stop_by_signal(self, signum):
        """
        通过信号停止
        :param signum:
        :return:
        """
        self.enable = False

        # 如果是终端直接CTRL-C，子进程自然会在父进程之后收到INT信号，不需要再写代码发送
        # 如果直接kill -INT $parent_pid，子进程不会自动收到INT
        # 所以这里可能会导致重复发送的问题，重复发送会导致一些子进程异常，所以在子进程内部有做重复处理判断。
        processes = self.worker_processes + [self.proxy_process]

        for p in processes:
            if p:
                p.send_signal(signum)

        if self.app.config['STOP_TIMEOUT'] is not None:
            self._kill_processes_later(processes, self.app.config['STOP_TIMEOUT'])

    def _handle_proc_signals(self):
        def stop_handler(signum, frame):
            """
            等所有子进程结束，父进程也退出
            """
            self._stop_by_signal(signum)

        def safe_reload_handler(signum, frame):
            """
            让所有子进程重新加载
            """
            self._reload_workers()

        # INT, QUIT为强制结束
        signal.signal(signal.SIGINT, stop_handler)
        signal.signal(signal.SIGQUIT, stop_handler)
        # TERM为安全结束
        signal.signal(signal.SIGTERM, stop_handler)
        # HUP为热更新
        signal.signal(signal.SIGHUP, safe_reload_handler)
