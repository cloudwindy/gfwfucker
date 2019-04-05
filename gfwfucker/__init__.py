"""
gfwfucker - A tool to bypass GFW!
"""
from hashlib  import md5
from asynchat import asyn_chat
from asyncore import dispatcher, loop
from logging  import basicConfig, getLogger, DEBUG, INFO, WARNING, ERROR, CRTITCAL

__author__ = 'cloudwindy'
__version__ = '1.0'

__all__ = ['GFWFucker']

# ----- config -----

# usage: size of each message from remote server
BUFFER_SIZE = 4096
# usage: size of reqest queue
BACKLOG     = 16

# ----- protocol -----

# sender: client
# usage: keep connection alive
# data: none
# response: HEARTBEAT
HEARTBEAT   = b'\x00'

# sender: client
# usage: log in the server
# data: password's md5
# response: SUCCESS or FAILURE
HANDSHAKE   = b'\x01'

# sender: client
# usage: connect a server
# data: target IP and port
# response: SUCCESS and connection ID(int, an ID for a connection) or FAILURE
CONNECT     = b'\x02'

# sender: client
# usage: send messages to a connected server
# data: given connection ID and messages
# response: SUCCESS or FAILURE
SEND        = b'\x03'

# sender: server
# usage: send recieved messages from a connected server
# data: given connection ID and messages
# response: SUCCESS or FAILURE
FORWARD     = b'\x04'

# sender: client or server
# usage: disconnect a connected server
# data: given connection ID
# response: DISCONNECT
DISCONNECT  = b'\x05'

# sender: client
# usage: quit the server
# data: none
# response: QUIT
QUIT        = b'\x06'

# sender: client or server
# usage: opeartion succeeded or failed
# data: (optional)str, reaseon
SUCCESS     = b'\xfe'
FAILURE     = b'\xff'

# ----- code ------

# usage: main 
def main(addr, port, password):
    GFWFucker('0.0.0.0', 8964, 'FuckYouGFW')
    loop()

class GFWFucker(dispatcher):
    def __init__(self, addr, port, password):
        dispatcher.__init__(self)
        md5_obj = md5()
        md5_obj.update(password.encode())
        self.password = md5_obj.digest()
        self.create_socket()
        self.set_reuse_addr()
        self.bind((addr, port))
        self.listen(BACKLOG)
    def handle_accept(self):
        (conn, addr) = self.accept()
        ClientHandler(conn, self.password)
    def handle_close(self):
        self.close()

# usage: handle a client
class ClientHandler(dispatcher):
    def __init__(self, cli, password):
        dispatcher.__init__(self, cli)
        self.cli = cli
        self.srv = RemoteHandler(self)
        self.password = password
        self.buf = bytes()
    def readable(self):
        return True
    def writable(self):
        return len(self.buf) > 0
    def send_pack(self, command, data = b''):
        self.buf += command
        self.buf += int2bytes(len(data)))
        self.buf += data
    def recv_pack(self):
        self.command = self.cli.recv(1)
        data_len = bytes2int(self.cli.recv(4))
        self.data = self.cli.recv(data_len)
    def handle_connect(self):
        pass
    def handle_read(self):
        
        if self.command == HEARTBEAT:
            self.heartbeat()
        elif self.command == HANDSHAKE:
            self.send_pack(FAILURE, b'Cannot handshake twice')
        elif self.command == CONNECT:
            self.remote_connect()
        elif self.command == SEND:
            self.remote_send()
        elif self.command == QUIT:
            self.close()
        else:
            self.send_pack(FAILURE, b'Unknown command')
    def handle_write(self):
        self.sendall(self.buf)
    def heartbeat(self):
        self.send_pack(HEARTBEAT)
    def handshake(self):
        while True:
            self.recv()
            if self.command == HANDSHAKE:
                if self.data == self.password:
                    self.send_pack(SUCCESS)
                    break
                else:
                    self.send_pack(FAILURE, b'Authentication failure')
            elif self.command == HEARTBEAT:
                self.heartbeat()
            elif self.command == QUIT:
                self.close()
            else:
                self.send(FAILURE, b'Unknown command(not logged in)')
    def remote_connect(self):
        addr = inet_ntoa(self.data[:4])
        port = bytes2int(self.data[4:8])
        try:
            srv_id = self.srv.get_id()
            self.srv.new(addr, port)
        except Exception as e:
            self.send(FAILURE, repr(e))
        else:
            self.send(SUCCESS, srv_id)
    def remote_send(self):
        srv_id = bytes2int(self.data[:4])
        try:
            self.srv.send(srv_id, self.data[4:])
        except Exception as e:
            self.send(FAILURE, repr(e))
    def handle_close(self):
        self.send(QUIT, b'Server disconnected')
        self.srv.close()
        self.cli.close()
        raise BreakException()

# usage: handle remote connection handlers
class RemoteHandlerList:
    def __init__(self, cli):
        self.srv_list = []
    def get_id(self):
        return len(self.srv_list)
    def new(self, )
# usage: handle client's sigle connection with remote server
class RemoteHandler(dispatcher):
    def __init__(self, addr, port, forwarder):
        dispatcher.__init__(self)
        self.create_socket()
        self.
        self.forward = forwarder
        self.buf = bytes()
    def readable(self):
        return True
    def writable(self):
        return len(self.buf) > 0
    def handle_connect(self):
        self.connect((self.addr, self.port))
    def handle_send(self):
        self.sendall(self.buf)
    def handle_read(self):
        buf = self.recv(BUFFER_SIZE)
        self.forward(buf)
    def handle_close(self):
        self.close()

# usage: change between int and bytes
def int2bytes(num):
    return int.to_bytes(num, 4, 'big')
def bytes2int(num):
    return int.from_bytes(num, 4, 'big')

# usage: break
class BreakException(Exception):
    pass