'''
 命令所对应的数据长度

 !0 固定长度
  0 不要recv
 -1 自动协商(在数据中加入数据长度)
'''
LENS = {}

'''
 客户端 -> 客户端
       ^ 心跳
 用途: 保持连接
 数据: 任意
 长度: 任意
 回应: HEARTBEAT
'''
HEARTBEAT       = b'\x00'
LENS[HEARTBEAT] = -1

'''
 客户端 -> 客户端
       ^ 握手
 用途: 认证
 数据: 密码 + 当前距2020-01-01 00:00:00的秒数
 长度:  16                4
 回应: 无论是成功还是失败都不回应
'''
HANDSHAKE       = b'\x01'
LENS[HANDSHAKE] = 20

'''
 客户端 -> 客户端
       ^ 建立连接
 用途: 建立到远端服务器的连接
 数据: IP地址 + 端口
 长度:   4      2
 回应: SUCCESS + ConnectionID 或 FAILURE
'''
CONNECT       = b'\x02'
LENS[CONNECT] = 6

'''
 客户端 -> 客户端
       ^ 发送
 用途: 发送数据包
 数据: 长度 + ConnectionID  + 内容
 长度:  4         4           n
 回应: 无
'''
SEND       = b'\x03'
LENS[SEND] = -1

'''
 客户端 <- 服务端
        ^ 转发
 用途: 转发数据包
 数据:  长度 + ConnectionID + 内容
 长度:   4         4          n
 回应: 无
'''
FORWARD       = b'\x04'
LENS[FORWARD] = -1

'''
 客户端 <-> 服务端
        ^ 断开连接
 用途: 断开指定ConnectionID的连接
 数据: ConnectionID
 长度:       4
 回应: 无
'''
DISCONNECT       = b'\x05'
LENS[DISCONNECT] = 4

'''
 客户端 -> 服务端
       ^ 退出
 用途: 退出服务器
 数据: 无
 长度: 0
 回应: 都退出服务器了 怎么可能还有回应
'''
QUIT       = b'\x06'
LENS[QUIT] = 0

'''
 客户端 <-> 服务端
        ^ 成功/失败
 用途: 表明上次操作成功与否
 数据: 如果有消息: 长度 + 消息
 长度:             4     n
 数据: 如果无消息: 0
 回应: 这个命令就是用于回应的...
'''
SUCCESS       = b'\xfe'
FAILURE       = b'\xff'
LENS[SUCCESS] = -1
LENS[FAILURE] = -1