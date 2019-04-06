"""
gfwfucker - A tool to bypass GFW!
"""
from socket   import socket, inet_ntoa
from hashlib  import md5
from logging  import basicConfig, getLogger, DEBUG, INFO
from asyncio  import run, open_connection, start_server
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
# usage: size of each message from remote server
BUFFER_SIZE   = 4096
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
    def __init__(self, conn_or_addr):
        if isinstance(conn_or_addr, socket):
            dispatcher.__init__(self, conn_or_addr)
        elif isinstance(conn_or_addr, tuple):
            dispatcher.__init__(self)
            self.create_socket()
            self.connect((conn_or_addr[0], conn_or_addr[1]))
        self.log = getLogger(self.__class__.__name__)
    # ----- override dispatcher -----
    def readable(self):
        return True
    def writable(self):
        return len(self.send_buf) > 0
    def handle_connect(self):
        pass
    def handle_send(self):
        num = self.send(self.send_buf)
        self.send_buf = self.send_buf[num:]
    def handle_read(self):
        self.recv_raw(BUFFER_SIZE)
    def handle_close(self):
        self.close()
    # ----- network traffic -----
    def send_raw(self, msg):
        """
        A -> B
          ^ raw
        """
        self.send(msg)
    def recv_raw(self, len):
        """
        A <- B
           ^ raw
        """
        try:
            self.recv_buf += self.recv(BUFFER_SIZE)
        except BlockingIOError:
            pass
    def send_pack(self, command, data = b''):
        """
        A -> B
          ^ packed
        """
        self.send_buf += command
        self.send_buf += int2bytes(len(data))
        self.send_buf += data
    def recv_pack(self):
        """
        A <- B
           ^ packed
        """
        try:
            self.command = self.recv(1)
            data_len = bytes2int(self.recv(4))
            self.data = self.recv(data_len)
        except BlockingIOError:
            pass
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

def int2bytes(num):
    """
    int -> bytes
        ^ encode
    """
    return int.to_bytes(num, 4, 'big')

def bytes2int(num):
    """
    bytes -> int
          ^ decode
    """
    return int.from_bytes(num, 4, 'big')

def str2md5(s):
    """
    password -> md5
             ^ md5 encode
    """
    md5_obj = md5()
    md5_obj.update(s.encode())
    return md5_obj.digest()
# ----- client -----

class GFWFuckerHTTPLocal(dispatcher):
    """
    local - client - server - remote
          ^ HTTP local handler
    """
    def __init__(self, addr, port):
        dispatcher.__init__(self)
class GFWFuckerSOCKSLocal(dispatcher):
    """
    local - client - server - remote
          ^ SOCKS local handler
    """
    def __init__(self, addr, port):
        dispatcher.__init__(self)
class GFWFuckerClient(BaseHandler):
    """
    local - client - server - remote
                   ^ connect handler
    """
    def __init__(self, addr, port, password):
        BaseHandler.__init__(self, (addr, port))
        self.is_verified = False
        self.send_pack(HANDSHAKE, str2md5(password))
        self.recv_pack()
        if self.command == FAILURE:
            self.c('Handshake failed! Reason: ' + self.data.encode())
    def handle_read(self):
        self.recv_pack()
        
    def forward(self):
        pass

# ----- server -----

class GFWFuckerServer:
    """
    local - client - server - remote
                   ^ accept handler(server)
    """
    def __init__(self, host, port, password):
        start_server(self.accept, host, port)
        self.password = str2md5(password)
        self.log = getLogger('MainServer')
    def accept(self, reader, writer):
        ClientHandler(conn, self.password)

class ClientHandler(BaseHandler):
    """
    local - client - server - remote
                   ^ client handler
    """
    def __init__(self, cli, password):
        BaseHandler.__init__(self, cli)
        self.srv = RemoteHandlerList(self.remote_forward)
        self.password = password
        self.verified = False
    def handle_read(self):
        if not self.verified:
            self.handshake()
        else:
            self.recv_pack()
            if self.command == HEARTBEAT:
                self.heartbeat()
            elif self.command == CONNECT:
                self.remote_connect()
            elif self.command == SEND:
                self.remote_send()
            elif self.command == QUIT:
                self.close()
            elif self.command == SUCCESS:
                pass
            elif self.command == FAILURE:
                self.e(self.data.encode())
            else:
                self.send_pack(FAILURE, b'Unknown command')
    def heartbeat(self):
        self.send_pack(HEARTBEAT)
    def handshake(self):
        self.recv_pack()
        if self.command == HANDSHAKE:
            if self.data == self.password:
                self.send_pack(SUCCESS)
                self.verified = True
            else:
                self.send_pack(FAILURE, b'Authentication failure (%s != %s)' % (self.data, self.password))
        elif self.command == HEARTBEAT:
            self.heartbeat()
        elif self.command == QUIT:
            self.close()
        else:
            self.send_pack(FAILURE, b'Unknown command(not logged in)')
    def remote_connect(self):
        addr = inet_ntoa(self.data[:4])
        port = bytes2int(self.data[4:8])
        srv_id = 0
        try:
            srv_id = self.srv.get_id()
            self.srv.new(addr, port)
        except Exception as e:
            self.send_pack(FAILURE, repr(e))
        else:
            self.send_pack(SUCCESS, srv_id)
    def remote_send(self):
        srv_id = bytes2int(self.data[:4])
        try:
            self.srv.send(srv_id, self.data[4:])
        except Exception as e:
            self.send_pack(FAILURE, repr(e))
    def remote_forward(self, msg):
        self.send_pack(FORWARD, msg)
    def handle_close(self):
        self.send_pack(QUIT, b'Server disconnected')
        self.srv.close_all()
        self.close()

class RemoteHandlerList:
    """
    local - client - server - remote
                            ^ remote handler list
    """
    def __init__(self, forwarder):
        self.forwarder = forwarder
        self.srv_list = []
    def get_id(self):
        return len(self.srv_list)
    def new(self, addr, port):
        self.srv_list[self.get_id()] = RemoteHandler(addr, port, self.forwarder)
    def send(self, srv_id, msg):
        self.srv_list[srv_id].send_raw(msg)
    def close(self, srv_id):
        self.srv_list[srv_id].close()
    def close_all(self):
        for srv in self.srv_list:
            srv.close()

class RemoteHandler(BaseHandler):
    """
    local - client - server - remote
                            ^ remote handler
    """
    def __init__(self, addr, port, forwarder):
        BaseHandler.__init__(self, (addr, port))
        self.forward = forwarder
    def handle_read(self):
        self.recv_raw(BUFFER_SIZE)
        self.forward(self.recv_buf)

if __name__ == '__main__':
    main()