from asyncio import open_connection, sleep
from logging import getLogger

from gfwfucker.tools    import enc, dec
from gfwfucker.config   import EVENT_TIME
from gfwfucker.protocol import *

__all__ = ['BaseHandler', 'ForwarderManager', 'BaseLogger']

class BaseHandler:
    """
    角色1 send_pack / recv_pack
    客户端/服务端 -> 服务端/客户端
                ^ 基础协议处理器
    
    接收命令及数据 对发送的数据包进行封包
    对收到的数据包进行解包 返回命令及数据

    包格式 (详情参见protocol.py)
    命令 数据
     1    n

    角色2 send_raw / recv_raw
    一端 -> 另一端
         ^ 基本的连接处理器
    
    发送/接受任意格式的数据 不做额外处理

    参数: 读取接口 写入接口
    """
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
    async def send_raw(self, data):
        await self.writer.awrite(data)
    async def recv_raw(self, data_len = -1):
        return await self.reader.read(data_len)
    async def send_pack(self, command, data = b''):
        await self.writer.awrite(command)
        await self.writer.awrite(enc(len(data)))
        await self.writer.awrite(data)
    async def recv_pack(self):
        self.command = await self.reader.readexactly(1)
        data_len = dec(await self.reader.readexactly(4))
        self.data = await self.reader.readexactly(data_len)
    async def close(self):
        await self.writer.aclose()

class ForwarderManager:
    """
    客户端 -> 服务端 -> 远端
          ^        ^ 转发管理器

    维护连接列表 根据ConnectionID分开连接
    与远端转发器是一对多的关系
    参数: 收到数据时回调的函数
    """
    def __init__(self, forwarder):
        self.forwarder = forwarder
        self.srv_list = []
    def add(self, addr, port):
        srv_latest_id = len(self.srv_list)
        self.srv_list[srv_latest_id] = ForwardHandler(addr, port, self.forwarder)
        return srv_latest_id
    async def serve(self, srv_id):
        srv = self.srv_list[srv_id]
        while True:
            await srv.run()
            await sleep(EVENT_TIME)
    async def forward(self, srv_id, data):
        await self.srv_list[srv_id].send_raw(data)
    async def close_forwarder(self, srv_id = None):
        if srv_id == None:
            for srv in self.srv_list:
                await srv.close()
            self.srv_list = []
        else:
            await self.srv_list[srv_id].close()


class ForwardHandler(BaseHandler):
    """
             /-> 远端
    服务端 <-+-> 远端
             \-> 远端
            ^ 远端转发器
    
    只处理一个连接
    参数: 远端地址 端口 每次收到数据时回调的函数
    """
    def __init__(self, addr, port, forwarder):
        reader, writer = open_connection(addr, port)
        BaseHandler.__init__(self, reader, writer)
        self._forward = forwarder
    async def forward(self):
        await self._forward(await self.recv_raw())

class BaseLogger:
    def __init__(self):
        self.log = getLogger(self.__class__.__name__)
    def d(self, msg):
        self.log.debug(msg)
    def i(self, msg):
        self.log.info(msg)
    def w(self, msg):
        self.log.warning(msg)
    def e(self, msg):
        self.log.error(msg)
    def ex(self, msg = ''):
        self.log.exception(msg)
    def c(self, msg):
        self.log.critical(msg)
