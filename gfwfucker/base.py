from gfwfucker.tools import enc, dec
from gfwfucker.config import EVENT_TIME
from asyncio  import open_connection, sleep
from logging  import getLogger

__all__ = ['BaseHandler', 'BaseForwarder', 'BaseLogger']

class BaseHandler:
    """
    one point -> another point
              ^ base handler
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

class BaseForwarder:
    """
    one point -> another point -> forwarded point
              ^       ->       ^ forwarder
    """
    def __init__(self, forwarder):
        self.forwarder = forwarder
        self.srv_list = []
    async def new(self, addr, port):
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
    async def close_forwarder(self, srv_id = -1):
        if srv_id == -1:
            for srv in self.srv_list:
                await srv.close()
        else:
            await self.srv_list[srv_id].close()

class ForwardHandler(BaseHandler):
    """
    local - client - server - remote
                            ^ remote handler
    """
    def __init__(self, addr, port, forwarder):
        reader, writer = open_connection(addr, port)
        BaseHandler.__init__(self, reader, writer)
        self.forward = forwarder
    async def run(self):
        while True:
            await self.forward(await self.recv_raw())

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
