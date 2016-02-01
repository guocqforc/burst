# -*- coding: utf-8 -*-

LOGGER_NAME = 'burst'

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
# 与maple不同，除了ask for job之外，都仅是转发，所以只要保证ask for job的cmd不要被使用就好
CMD_WORKER_ASK_FOR_JOB = -1

# worker监听的address状态
WORKER_ADDRESS_TPL = 'worker_%s.sock'

# 进程类型
PROC_TYPE_PROXY = 1
PROC_TYPE_WORKER = 2
