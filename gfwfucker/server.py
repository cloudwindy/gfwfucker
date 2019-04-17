from gfwfucker.base import BaseHandler, BaseForwarder, BaseLogger
from gfwfucker.protocol import *
from gfwfucker.tools import enc, dec, md5
from socket import inet_ntoa
from asyncio  import open_connection, start_server, IncompleteReadError

__all__ = ['GFWFuckerServer']

class GFWFuckerServer:
    """
    local - client - server - remote
                       ^ i'm a server
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

class ClientHandler(BaseHandler, BaseForwarder, BaseLogger):
    """
    local - client - server - remote
                   ^ client handler
    """
    def __init__(self, reader, writer):
        BaseHandler.__init__(self, reader, writer)
        BaseForwarder.__init__(self, self._forward)
        BaseLogger.__init__(self)
    async def __call__(self, password):
        try:
            await self._handshake(password)
            await self._serve()
        except IncompleteReadError:
            self.w('Client exited unexceptedly')
    async def _handshake(self, password):
        while True:
            await self.recv_pack()
            if self.command == HEARTBEAT:
                await self._heartbeat()
            elif self.command == HANDSHAKE:
                if self.data == password:
                    await self.send_pack(SUCCESS)
                    break
                else:
                    await self.send_pack(FAILURE, b'Authentication failure (%s != %s)' % (self.data, password))
            elif self.command == QUIT:
                await self._close()
            else:
                await self.send_pack(FAILURE, b'Unknown command(while handshaking)')
    async def _serve(self):
        while True:
            await self.recv_pack()
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
                self.e(self.data.encode())
            else:
                await self.send_pack(FAILURE, b'Unknown command')
    async def _heartbeat(self):
        await self.send_pack(HEARTBEAT)
    async def _connect(self):
        addr = inet_ntoa(self.data[:4])
        port = dec(self.data[4:8])
        try:
            srv_id = self.new(addr, port)
            await self.send_pack(SUCCESS, srv_id)
        except Exception as e:
            await self.send_pack(FAILURE, repr(e))
            self.ex()
    async def _send(self):
        srv_id = dec(self.data[:4])
        try:
            await self.forward(srv_id, self.data[4:])
            await self.send_pack(SUCCESS, srv_id)
        except Exception as e:
            await self.send_pack(FAILURE, repr(e))
            self.ex()
    async def _disconnect(self):
        srv_id = dec(self.data[:4])
        await self.close_forwarder(srv_id)
    async def _forward(self, data):
        await self.send_pack(FORWARD, data)
    async def _close(self):
        await self.send_pack(QUIT, b'Server disconnected')
        await self.close()