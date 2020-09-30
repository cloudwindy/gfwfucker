from socket             import inet_ntoa
from asyncio            import create_task, open_connection, start_server, IncompleteReadError

from cli2               import UIPrinter
from gfwfucker.base     import BaseHandler, BaseLogger, ForwarderManager, ForwardHandler
from gfwfucker.protocol import *
from gfwfucker.tools    import enc, dec, md5, pretty_hex

__all__ = ['GFWFuckerServer']

class GFWFuckerServer:
    """
    本地 - 客户端 - 服务端 - 远端
                    ^ 我是服务端
    
    接受客户端的连接并移交给客户端处理器
    """
    def __init__(self, host, port, password):
        self.host = host
        self.port = port
        self.password = md5(password)
    async def run(self):
        async with await start_server(self._handle, self.host, self.port) as srv:
            await srv.serve_forever()
    async def _handle(self, reader, writer):
        handle = ClientHandler(reader, writer)
        await handle(self.password)

class ClientHandler(BaseHandler, UIPrinter):
    """
    本地 - 客户端 - 服务端 - 远端
                ^ 客户端处理器
    
    每个客户端的处理流程
    """
    def __init__(self, reader, writer):
        BaseHandler.__init__(self, reader, writer)
        UIPrinter.__init__(self, '')
        self.fwd = ForwarderManager(self._forward)
    async def __call__(self, password):
        '''正常处理流程'''
        await self._handshake(password)
        await self._serve()
    async def _handshake(self, password):
        '''身份验证及加密握手流程'''
        while True:
            await self.recv_pack()
            if self.command == HANDSHAKE:
                if self.data == password:
                    # 验证通过
                    break
            else:
                self.fail(f'未知指令 {pretty_hex(self.command)}')
    async def _serve(self):
        '''服务流程'''
        while True:
            await self.recv_pack()
            {
                HEARTBEAT : self._heartbeat,
                CONNECT   : self._connect,
                SEND      : self._send,
                DISCONNECT: self._disconnect,
                QUIT      : self._close,
                FAILURE   : self._msg
            }.get(self.command)
            if self.command == HEARTBEAT:
                await self._heartbeat()
            elif self.command == CONNECT:
                await self._connect()
            elif self.command == SEND:
                await self._send()
            elif self.command == DISCONNECT:
                await self._disconnect()
            elif self.command == QUIT:
                await self._close()
            elif self.command == FAILURE:
                self.fail(self.data.encode())
            else:
                await self.send_pack(FAILURE, b'Unknown command')
    async def _heartbeat(self):
        await self.send_pack(HEARTBEAT)
    async def _connect(self):
        addr = inet_ntoa(self.data[:4])
        port = dec(self.data[4:8])
        try:
            srv_id = self.fwd.add(addr, port)
            await self.send_pack(SUCCESS, srv_id)
        except Exception as e:
            await self.send_pack(FAILURE, repr(e))
            self.ex()
    async def _send(self):
        srv_id = dec(self.data[:4])
        try:
            await self.fwd.forward(srv_id, self.data[4:])
            await self.send_pack(SUCCESS, srv_id)
        except Exception as e:
            await self.send_pack(FAILURE, repr(e))
            self.ex()
    async def _disconnect(self):
        srv_id = dec(self.data[:4])
        await self.fwd.close_forwarder(srv_id)
    async def _forward(self, data):
        await self.send_pack(FORWARD, data)
    async def _close(self):
        await self.send_pack(QUIT, b'Server disconnected')
        self.succ('客户端已退出')
        await self.close()