# -

## 命令表

| 命令 | 含义                       | 参数                        | 说明                                  |
| ---- | -------------------------- | --------------------------- | ------------------------------------- |
| EDG  | Edge Data Generation       | fileID count                | 生成测试数据                          |
| UED  | Upload Edge Data           | fileID                      | 上传数据                              |
| SCS  | Server Computation Service | fileID computationOperation | 服务端计算                            |
| DTE  | Delete the data file       | fileID                      | 删除服务端文件                        |
| AED  | Active Edge Devices        | -                           | 显示在线边缘终端名称,IP:端口,加入时间 |
| OUT  | Exit edge network          | -                           | 退出边缘网络                          |
| ---- | -----------------          | -------------------         | ------------                          |
| UVF  | Upload Video File          | deviceName filename         | 推送视频文件                          |

## 命令参数

- Server

`python server.py server_port number_of_consecutive_failed_attempts`

- Client

`python client.py server_IP server_port client_udp_server_port`
