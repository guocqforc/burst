# burst

### 一. 概述

逻辑服务器框架。灵感来自于腾讯内部的SPP。


### 二. 模块介绍

进程主要分为 master、proxy、worker 3个部分。
网络部分使用twisted驱动。使用twisted的原因，一是为了简化代码，另一方面也是为了使mac/linux都可以直接运行。否则手写epoll的话，mac下就没法调试了。

1. master

    作为管理进程，负责管理proxy和worker进程的状态。例如proxy/worker异常死掉，master会负责重新拉起。

2. proxy

    网络进程，负责接收网络消息，并且将任务派发给worker进行处理，之后再返回给client端。  
    worker、master 均会与proxy建立连接。并均使用本地socket的方式。  
    proxy还支持bustctl的连接，可以进行worker数量配置，统计等操作。当然，需要在服务器启动的时候，打开ADMIN相关的配置。

3. worker

    工作进程，负责真正的任务处理。  
    为了简化模型，worker要求与http协议一样，仅支持一个或者无回应。当worker对proxy返回有内容的或者空回应时，会顺便告知proxy，worker状态已经回到idle状态，可以分配任务了。  
    而因为有这种应答的特性，所以proxy中对应的worker连接，并没有使用如 [maple](https://github.com/dantezhu/maple) 一样的client_id机制，而是直接将conn的连接弱引用存储在了proxy中对应的worker连接上。

4. burstctl

    管理工具，可以在线完成统计、配置变更、重启等操作。

    * change_group     修改group配置，比如workers数量
    * reload_workers   更新workers
    * restart_workers  重启workers.
    * stat             查看统计
    * stop             安全停止整个服务
    * version          版本号

    统计示例:

        /--------------------------------------------------------------------------------
        {
            "clients": 100,
            "busy_workers": {
                "1": 2,
                "10": 0
            },
            "idle_workers": {
                "1": 0,
                "10": 2
            },
            "pending_tasks": {
                "1": 97,
                "10": 0
            },
            "client_req": 19691,
            "client_rsp": 19592,
            "worker_req": 19594,
            "worker_rsp": 19592,
            "tasks_time": {
                "10": 19238,
                "50": 353,
                "100": 1
            }
        }
        --------------------------------------------------------------------------------/
    

### 三. 部署

以supervisor为例:

    [program:burst_server]
    environment=PYTHON_EGG_CACHE=/tmp/.python-eggs/
    directory=/data/release/prj
    command=python main.py
    user=dantezhu
    autorestart=true
    redirect_stderr=true


优雅重启:

    kill -HUP $master_pid

优雅停止:

    kill -TERM $master_pid

强制停止:

    kill -INT $master_pid
    kill -QUIT $master_pid


### 四. 注意

1. 配置要求

    group_id务必为数字类型，否则burstctl无法正确处理.

### 五. TODO

1. <del>支持修改worker数量后，优雅重启worker. 目前可行方案是通过burst ctl，但是ctl是连接到了proxy，貌似还不行</del>
2. 考虑group_conf和group_router怎么更好的重新载入
3. <del>考虑是不是要支持udp，似乎没法直接支持。其实调用方可以直接在前面建一个udp代理server即可</del>
4. 怎样在刚开始启动的时候，不报connect fail的错误
