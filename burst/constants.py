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


# worker的状态
WORKER_STATUS_IDLE = 1
WORKER_STATUS_BUSY = 2

# 进程类型
PROC_TYPE_MASTER = 'master'
PROC_TYPE_PROXY = 'proxy'
PROC_TYPE_WORKER = 'worker'


# 默认配置
DEFAULT_CONFIG = {
    # 是否调试模式
    'DEBUG': False,

    # 监听IP
    'HOST': '127.0.0.1',
    # 监听端口
    'PORT': 9900,

    # 进程名
    'NAME': NAME,

    # 分组进程配置:
    #    {
    #        $group_id: {
    #            count: 10,
    #        }
    #    }
    'GROUP_CONFIG': {
        1: {
            'count': 1,
        }
    },
    # 通过box路由group_id:
    #    def group_router(box):
    #        return group_id
    'GROUP_ROUTER': lambda box: 1,

    # 停止子进程超时(秒). 使用 TERM 进行停止时，如果超时未停止会发送KILL信号
    'STOP_TIMEOUT': None,

    # proxy<->worker之间通信的address模板
    'IPC_ADDRESS_TPL': '%s_ipc/' % NAME + '%s.sock',

    # proxy的backlog
    'PROXY_BACKLOG': 256,

    # worker<->proxy网络连接超时(秒), 包括 connect once，read once，write once
    'WORKER_CONN_TIMEOUT': 3,
    # 处理task超时(秒). 超过后worker会自杀. None 代表永不超时
    'WORK_TIMEOUT': None,
    # worker重连等待时间
    'WORKER_TRY_CONNECT_INTERVAL': 1,

    # 子进程标识进程类型的环境变量
    'CHILD_PROCESS_ENV_KEY': 'BURST_ENV',

    # 管理员，可以连接proxy获取数据
    # 管理员访问地址如 (127.0.0.1, 22222)
    'ADMIN_ADDRESS': None,
    'ADMIN_USERNAME': None,
    'ADMIN_PASSWORD': None,

    # 统计相关
    # 作业时间统计标准
    'TASKS_TIME_BENCHMARK': (10, 50, 100, 500, 1000, 5000),
}
