# burst
server framework. master, proxy and worker 


是否使用twisted的一个很大原因是，如果用twisted的话，mac下就可以直接用了。否则就要手写epoll。


### TODO

1. proxy支持多个监听地址
2. 支持修改worker数量后，优雅重启worker
