# -*- coding: utf-8 -*-

NAME = 'burst'

# 系统返回码
# 命令字不合法
RET_INVALID_CMD = -10000
# 系统内部异常
RET_INTERNAL = -10001
# admin用户验证失败
RET_ADIMN_AUTH_FAIL = -20000

# 内部使用的命令字
# 分配任务. 如果body里面带数据，说明是要写回；如果没有数据，说明只是要分配task
CMD_WORKER_TASK_ASSIGN = 100
# 任务完成
CMD_WORKER_TASK_DONE = 200
# 管理员命令
# 获取运行状态统计
CMD_ADMIN_SERVER_STAT = 20000


# 子进程城的环境变量
CHILD_ENV_KEY = 'BURST_ENV'

# 作业时间统计标准
TASKS_TIME_BENCHMARK = (10, 50, 100, 500, 1000, 5000)

# proxy<->worker之间通信的address模板
IPC_ADDRESS_TPL = '%s_ipc/' % NAME + '%s.sock'


# 默认backlog
PROXY_BACKLOG = 256


# worker的状态
WORKER_STATUS_IDLE = 1
WORKER_STATUS_BUSY = 2

# worker重连等待时间
WORKER_TRY_CONNECT_INTERVAL = 1

# 网络连接超时(秒)，包括 connect once，read once，write once
WORKER_CONN_TIMEOUT = 3


# 进程类型
PROC_TYPE_MASTER = 'master'
PROC_TYPE_PROXY = 'proxy'
PROC_TYPE_WORKER = 'worker'
