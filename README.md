# burst
server framework. master, proxy and worker 


是否使用twisted的一个很大原因是，如果用twisted的话，mac下就可以直接用了。否则就要手写epoll。


### TODO

1. 支持修改worker数量后，优雅重启worker. 目前可行方案是通过burst ctl，但是ctl是连接到了proxy，貌似还不行
