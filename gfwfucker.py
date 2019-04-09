"""
gfwfucker - A tool to bypass GFW!
"""
from socket   import socket, inet_ntoa
from hashlib  import md5
from logging  import basicConfig, getLogger, DEBUG, INFO
from asyncio  import run, open_connection, start_server, IncompleteReadError
#from asyncore import dispatcher, loop

__author__ = 'cloudwindy'
__version__ = '1.0'

__all__ = ['GFWFuckerServer', 'GFWFuckerClient']

# ----- config -----

# usage: running test
TEST_SERVER      = '127.0.0.1'
TEST_PORT        = 8964
TEST_PASSWORD    = 'FuckYouGFW'
TEST_HTTP_SERVER = '127.0.0.1'
TEST_HTTP_PORT   = 1080
# usage: size of reqest queue
BACKLOG       = 16

# ----- protocol -----

# sender: client
# usage: keep connection alive
# data: none
# response: HEARTBEAT
HEARTBEAT     = b'\x00'

# sender: client
# usage: log in the server
# data: password's md5
# response: SUCCESS or FAILURE
HANDSHAKE     = b'\x01'

# sender: client
# usage: connect a server
# data: target IP and port
# response: SUCCESS and connection ID(int, an ID for a connection) or FAILURE
CONNECT       = b'\x02'

# sender: client
# usage: send messages to a connected server
# data: given connection ID and messages
# response: SUCCESS or FAILURE
SEND          = b'\x03'

# sender: server
# usage: send recieved messages from a connected server
# data: given connection ID and messages
# response: SUCCESS or FAILURE
FORWARD       = b'\x04'

# sender: client or server
# usage: disconnect a connected server
# data: given connection ID
# response: DISCONNECT
DISCONNECT    = b'\x05'

# sender: client
# usage: quit the server
# data: none
# response: QUIT
QUIT          = b'\x06'

# sender: client or server
# usage: opeartion succeeded or failed
# data: (optional)str, reaseon
SUCCESS       = b'\xfe'
FAILURE       = b'\xff'

# ----- test main ------

# usage: only for test
def main():
    GFWFuckerServer(TEST_SERVER, TEST_PORT, TEST_PASSWORD)
    #GFWFuckerHTTPLocal(TEST_HTTP_SERVER, TEST_HTTP_PORT)
    #GFWFuckerClient(TEST_SERVER, TEST_PORT, TEST_PASSWORD)

# ----- explanation -----

# browser - GFWFuckerClient - GFWFuckerServer - www.google.com 
#    ^             ^                ^                 ^
#  local  -      client     -     server      -     remote
#         ^ raw             ^ encrypted       ^ raw

# ----- base -----

class BaseHandler:
    """
    one point -> another point
              ^ base handler
    """
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self.log = getLogger(self.__class__.__name__)
    # ----- network traffic -----
    async def send_raw(self, data):
        await self.writer.awrite(data)
    async def recv_raw(self):
        return await self.reader.read()
    async def send_pack(self, command, data = b''):
        await self.writer.awrite(command)
        await self.writer.awrite(int2bytes(len(data)))
        await self.writer.awrite(data)
    async def recv_pack(self):
        self.command = await self.reader.readexactly(1)
        data_len = bytes2int(await self.reader.readexactly(4))
        self.data = await self.reader.readexactly(data_len)
    async def close(self):
        await self.writer.aclose()
    # ----- log -----
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

class BaseHandlerWithForwarder(BaseHandler):
    """
    local - client - server - remote
    ^               ^ ->  <- ^ forwarder
    """
    def __init__(self, reader, writer, forwarder):
        BaseHandler.__init__(self, reader, writer)
        self.forwarder = forwarder
        self.srv_list = []
    def get_id(self):
        return len(self.srv_list)
    async def new(self, addr, port):
        self.srv_list[self.get_id()] = await RemoteHandler(addr, port, self.forwarder)
    async def forward(self, srv_id, data):
        await self.srv_list[srv_id].send_raw(data)
    def close_forwarder(self, srv_id = -1):
        if srv_id == -1:
            for srv in self.srv_list:
                srv.close()
        else:
            self.srv_list[srv_id].close()

class RemoteHandler(BaseHandler):
    """
    local - client - server - remote
                            ^ remote handler
    """
    async def __init__(self, addr, port, forwarder):
        BaseHandler.__init__(self, addr, port)
        self.forward = forwarder
    async def read(self):
        data = await self.recv_raw()
        await self.forward(data)
    async def write(self, data):
        await self.send_raw(data)

# ----- server -----

PASSWORD = b''

async def GFWFuckerServer(host, port, password):
    """
    local - client - server - remote
                       ^ i'm a server
    """
    PASSWORD = str2md5(password)
    async with await start_server(ClientHandler, host, port) as srv:
        await srv.serve_forever()

class ClientHandler(BaseHandlerWithForwarder):
    """
    local - client - server - remote
                   ^ client handler
    """
    async def __init__(self, reader, writer):
        BaseHandlerWithForwarder.__init__(self, reader, writer, self._forward)
        self.password = PASSWORD
        await self._handshake()
        await self._serve()
    async def _handshake(self):
        while True:
            await self.recv_pack()
            if self.command == HEARTBEAT:
                await self._heartbeat()
            elif self.command == HANDSHAKE:
                if self.data == self.password:
                    await self.send_pack(SUCCESS)
                    break
                else:
                    await self.send_pack(FAILURE, b'Authentication failure (%s != %s)' % (self.data, self.password))
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
        port = bytes2int(self.data[4:8])
        try:
            srv_id = self.get_id()
            self.new(addr, port)
            await self.send_pack(SUCCESS, srv_id)
        except Exception as e:
            await self.send_pack(FAILURE, repr(e))
            self.ex()
    async def _send(self):
        srv_id = bytes2int(self.data[:4])
        try:
            await self.forward(srv_id, self.data[4:])
            await self.send_pack(SUCCESS, srv_id)
        except Exception as e:
            await self.send_pack(FAILURE, repr(e))
            self.ex()
    async def _forward(self, data):
        await self.send_pack(FORWARD, data)
    async def _close(self):
        await self.send_pack(QUIT, b'Server disconnected')
        await self.close()

# ----- client -----

class GFWFuckerHTTPLocal(BaseHandlerWithForwarder):
    """
    local - client - server - remote
          ^ HTTP local handler
    """
    def __init__(self, addr, port):
        BaseHandlerWithForwarder.__init__(self)
class GFWFuckerSOCKSLocal(BaseHandlerWithForwarder):
    """
    local - client - server - remote
          ^ SOCKS local handler
    """
    def __init__(self, addr, port):
        BaseHandlerWithForwarder.__init__(self)
class GFWFuckerClient(BaseHandler):
    """
    local - client - server - remote
                   ^ connect handler
    """
    def __init__(self, addr, port, password):
        BaseHandler.__init__(self, addr, port)
        self.is_verified = False
        self.send_pack(HANDSHAKE, str2md5(password))
        self.recv_pack()
        if self.command == FAILURE:
            self.c('Handshake failed! Reason: ' + self.data.encode())
    def handle_read(self):
        self.recv_pack()
        
    def forward(self):
        pass

def int2bytes(num):
    return int.to_bytes(num, 4, 'big')
def bytes2int(num):
    return int.from_bytes(num, 4, 'big')
def str2md5(s):
    md5_obj = md5()
    md5_obj.update(s.encode())
    return md5_obj.digest()

if __name__ == '__main__':
    main()