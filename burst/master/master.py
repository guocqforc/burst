# -*- coding: utf-8 -*-

import os
import copy
import json
import sys
import subprocess
import time
import signal
import setproctitle
from .. import constants


class Master(object):
    """
    master相关
    """

    type = constants.PROC_TYPE_MASTER

    app = None

    enable = True

    # 子进程列表
    processes = None

    def __init__(self, app):
        """
        构造函数
        :return:
        """
        self.app = app
        self.processes = []

    def run(self):
        setproctitle.setproctitle(self.app.make_proc_name(self.type))

        self._handle_proc_signals()

        self._spawn_workers()

    def _spawn_workers(self):
        def start_child_process(proc_env):
            # 要传入group_id
            worker_env = copy.deepcopy(os.environ)
            worker_env.update({
                constants.CHILD_ENV_KEY: json.dumps(proc_env)
            })

            args = [sys.executable] + sys.argv
            inner_p = subprocess.Popen(args, env=worker_env)
            inner_p.proc_env = proc_env
            return inner_p

        proc_env = dict(
            type=constants.PROC_TYPE_PROXY
        )
        p = start_child_process(proc_env)
        self.processes.append(p)

        for group_id, group_info in self.app.group_conf.items():
            proc_env = dict(
                type=constants.PROC_TYPE_WORKER,
                group_id=group_id,
            )

            # 进程个数
            for it in xrange(0, group_info['count']):
                p = start_child_process(proc_env)
                self.processes.append(p)

        while 1:
            for idx, p in enumerate(self.processes):
                if p and p.poll() is not None:
                    # 说明退出了
                    proc_env = p.proc_env
                    self.processes[idx] = None

                    if self.enable:
                        # 如果还要继续服务
                        p = start_child_process(proc_env)
                        self.processes[idx] = p

            if not filter(lambda x: x, self.processes):
                # 没活着的了
                break

            # 时间短点，退出的快一些
            time.sleep(0.1)

    def _handle_proc_signals(self):
        def exit_handler(signum, frame):
            self.enable = False

            # 如果是终端直接CTRL-C，子进程自然会在父进程之后收到INT信号，不需要再写代码发送
            # 如果直接kill -INT $parent_pid，子进程不会自动收到INT
            # 所以这里可能会导致重复发送的问题，重复发送会导致一些子进程异常，所以在子进程内部有做重复处理判断。
            for p in self.processes:
                if p:
                    p.send_signal(signum)

            # https://docs.python.org/2/library/signal.html#signal.alarm
            if self.app.stop_timeout is not None:
                signal.alarm(self.app.stop_timeout)

        def final_kill_handler(signum, frame):
            if not self.enable:
                # 只有满足了not enable，才发送term命令
                for p in self.processes:
                    if p:
                        p.send_signal(signal.SIGKILL)

        def safe_stop_handler(signum, frame):
            """
            等所有子进程结束，父进程也退出
            """
            self.enable = False

            for p in self.processes:
                if p:
                    p.send_signal(signal.SIGTERM)

            if self.app.stop_timeout is not None:
                signal.alarm(self.app.stop_timeout)

        def safe_reload_handler(signum, frame):
            """
            让所有子进程重新加载
            """
            for p in self.processes:
                if p:
                    p.send_signal(signal.SIGHUP)

        # INT, QUIT为强制结束
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGQUIT, exit_handler)
        # TERM为安全结束
        signal.signal(signal.SIGTERM, safe_stop_handler)
        # HUP为热更新
        signal.signal(signal.SIGHUP, safe_reload_handler)
        # 最终判决，KILL掉子进程
        signal.signal(signal.SIGALRM, final_kill_handler)
