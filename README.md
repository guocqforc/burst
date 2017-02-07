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
    支持tcp/udp监听。
    worker、master 均会与proxy建立连接。并均使用本地socket的方式。  
    proxy还支持bustctl的连接，可以进行worker数量配置，统计等操作。当然，需要在服务器启动的时候，打开ADMIN相关的配置。

3. worker

    工作进程，负责真正的任务处理。  
    为了简化模型，worker要求与http协议一样，仅支持一个或者无回应。当worker对proxy返回有内容的或者空回应时，会顺便告知proxy，worker状态已经回到idle状态，可以分配任务了。  
    而因为有这种应答的特性，所以proxy中对应的worker连接，并没有使用如 [maple](https://github.com/dantezhu/maple) 一样的client_id机制，而是直接将conn的连接弱引用存储在了proxy中对应的worker连接上。

4. burstctl

    管理工具，可以在线完成统计、配置变更、重启等操作。

    * change           修改group配置，比如workers数量
    * clear            清空消息队列
    * reload           更新workers
    * stat             查看统计
    * stop             安全停止整个服务
    * version          版本号

    统计示例:
    
        {
            "clients": 16,
            "workers": {
                "all": 8,
                "1": 8
            },
            "busy_workers": {
                "all": 0,
                "1": 0
            },
            "idle_workers": {
                "all": 8,
                "1": 8
            },
            "pending_tasks": {
                "all": 0,
                "1": 0
            },
            "client_req": 37983,
            "client_rsp": 0,
            "worker_req": {
                "all": 37983,
                "1": 37983
            },
            "worker_rsp": {
                "all": 37983,
                "1": 37983
            },
            "tasks_time": {
                "10": 4484,
                "50": 1267,
                "100": 775,
                "500": 30234,
                "1000": 638,
                "5000": 584,
                "more": 1
            }
        }


### 三. 部署

以supervisor为例:

    [program:burst_server]
    environment=PYTHON_EGG_CACHE=/tmp/.python-eggs/
    directory=/data/release/prj
    command=python main.py
    user=dantezhu
    autorestart=true
    redirect_stderr=true
    stopwaitsecs=10

优雅重启:

    kill -HUP $master_pid

    burstctl reload

优雅停止:

    kill -TERM $master_pid

    burstctl stop

强制停止:

    kill -INT $master_pid
    kill -QUIT $master_pid


### 四. 设计思路

1. 优雅重启

maple的优雅重启比较简单，即将worker安全停止后，master自然会将停止的worker重新启动，从而实现优雅重启.  
但是后来发现一个问题，即worker的启动速度越来越慢，主要原因是当应用越来越复杂时，import的库和模块会越来越多。尤其多个worker同时启动时，时间更长。  
这在maple中还是能够接受的，因为maple的worker其实是无状态的，所以无非是启动两套workers，每套workers单独优雅重启就足以不影响业务。

但是在burst中，这个是接受不了的，因为burst的workers是分组的，如果用上面的方法启动，就可以导致某个组内的消息一直被堵塞。

所以，我实现了另一套方案:

    1. master收到HUP信号后，先标识自己的状态为reload中，并通知proxy也变成reload中状态。
    2. master启动一批worker，但是作为替补worker存在，不替换原有的worker。
    3. proxy在reload状态下，将收到的新worker连接也都放到替补workers中去。
    4. proxy在收到client消息、worker工作完成消息、worker建立新连接消息后，都去判断替补worker是否已经达到替换老workers的条件，如果已经达到则替换老workers，并通过master_connection向master发送消息，告知master可以替换掉老workers了。表示自己为非reload状态。
    5. master替换掉老的workers，并向老的workers发送TERM信号。标识自己状态为非reload状态。


### 五. 注意

1. 配置要求

    group_id务必为数字类型，否则burstctl无法正确处理.

2. 使用udp监听的时候，由于udp的特性，clients数量无法统计.

### 六. TODO

1. <del>支持修改worker数量后，优雅重启worker. 目前可行方案是通过burst ctl，但是ctl是连接到了proxy，貌似还不行</del>
2. 考虑group_conf和group_router怎么更好的热加载
3. <del>考虑是不是要支持udp，似乎没法直接支持。其实调用方可以直接在前面建一个udp代理server即可</del>
4. <del>怎样在刚开始启动的时候，不报connect fail的错误</del>
5. <del>client.timeout配置</del>
6. <del>burstctl支持clear某个group的消息</del>
