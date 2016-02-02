# -*- coding: utf-8 -*-

NAME = 'burst'

# worker的状态
WORKER_STATUS_IDLE = 1
WORKER_STATUS_BUSY = 2

# 系统返回码
RET_INVALID_CMD = -10000
RET_INTERNAL = -10001

# 默认backlog
PROXY_BACKLOG = 256

# 重连等待时间
TRY_CONNECT_INTERVAL = 1

# worker的group_id env
CHILD_ENV_KEY = 'BURST_ENV'

# 网络连接超时(秒)，包括 connect once，read once，write once
CONN_TIMEOUT = 3

# 内部使用的命令字
# 分配任务. 如果body里面带数据，说明是要写回；如果没有数据，说明只是要分配job
CMD_WORKER_TASK_ASSIGN = 100
# 任务完成
CMD_WORKER_TASK_DONE = 200

# proxy<->worker之间通信的address模板
IPC_ADDRESS_TPL = NAME + '_%s.sock'

# 进程类型
PROC_TYPE_MASTER = 'master'
PROC_TYPE_PROXY = 'proxy'
PROC_TYPE_WORKER = 'worker'

