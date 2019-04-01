"""
gfwfucker - A tool to bypass GFW!
"""
from socket                import socket, inet_ntoa
from hashlib               import md5
from multiprocessing.dummy import Process, Pool

__author__ = 'cloudwindy'
__version__ = '1.0'

__all__ = ['GFWFucker']

# config part
BACKLOG = 128

# protocol part

# usage: salt in password's md5
SALT = b'FuckYouGFW'

# usage: max packet length's length
LEN  = 4

# sender: client
# usage: keep connection alive
# data: none
# response: HEARTBEAT
HEARTBEAT  = b'\x00'

# sender: client
# usage: log in the server
# data: password's md5
# response: SUCCESS or FAILURE
HANDSHAKE  = b'\x01'

# sender: client
# usage: connect a server
# data: target IP and port
# response: SUCCESS and connection ID(int, an ID for a connection) or FAILURE
CONNECT    = b'\x02'

# sender: client
# usage: send messages to a connected server
# data: given connection ID and messages
# response: none
SEND       = b'\x03'

# sender: client
# usage: get recieved messages from a connected server
# data: given connection ID and messages
# response: none
RECV       = b'\x04'

# sender: client or server
# usage: disconnect a connected server
# data: given connection ID
# response: none
DISCONNECT = b'\x05'

# sender: client
# usage: quit the server
# data: none
# response: QUIT
QUIT       = b'\x06'

# sender: client or server
# usage: opeartion succeeded or failed
# data: (optional)str, reaseon
SUCCESS    = b'\xfe'
FAILURE    = b'\xff'

class BreakException(Exception):
    pass
class GFWFucker:
    def __init__(self, addr, port, password):
        self.srv = socket()
        self.srv.bind((addr, port))
        md5_obj = md5(SALT)
        md5_obj.update(password.encode())
        self.password = md5_obj.digest()
    def fuck(self):
        self.srv.listen()
        pool = Pool(BACKLOG)
        while True:
            cli = self.srv.accept()
            cli_sock = cli[0]
            cli_addr = '%s:%d' % cli[1]
            pool.apply_async(target = ClientHandler(cli_sock, self.password))
        pool.close()
        pool.join()
class ClientHandler:
    def __init__(self, cli, password):
        self.srv_lastest_id = 0
        self.srv_list = []
        self.cli = cli
        self.password = password
    def __call__(self):
        try:
            self.handshake()
            while True:
                self.recv()
                if self.command == HEARTBEAT:
                    self.heartbeat()
                elif self.command == HANDSHAKE:
                    self.send(FAILURE, b'Cannot handshake twice')
                elif self.command == CONNECT:
                    self.remote_connect()
                elif self.command == SEND:
                    self.remote_send()
                elif self.command == RECV:
                    self.remote_recv()
                elif self.command == QUIT:
                    self.close()
        except BreakException:
            pass
        except Exception as e:
            print(repr(e))
            try:
                self.close()
            except BreakException:
                pass
    def heartbeat(self):
        self.send(HEARTBEAT)
    def handshake(self):
        while True:
            self.recv()
            if self.command == HANDSHAKE:
                if self.data == self.password:
                    self.send(SUCCESS)
                    break
                else:
                    self.send(FAILURE, b'Authentication failure')
            elif self.command == HEARTBEAT:
                self.heartbeat()
            elif self.command == QUIT:
                self.close()
            else:
                self.send(FAILURE, b'Not logged in')
    def remote_connect(self):
        addr = inet_ntoa(self.data[:4])
        port = int.from_bytes(self.data[4:8], 4, 'big')
        srv = socket()
        try:
            srv.connect((addr, port))
            self.srv_list[self.srv_lastest_id] = srv
            data = int.to_bytes(self.srv_lastest_id, LEN, 'big')
            self.send(SUCCESS, data)
            self.srv_lastest_id += 1
        except Exception as e:
            srv.send(FAILURE, repr(e))
    def remote_send(self):
        srv_id = int.from_bytes(self.data[:4], 4, 'big')
        srv = self.srv_list[srv_id]
        try:
            srv.send(self.data[4:])
        except Exception as e:
            self.send(FAILURE, repr(e))
    def remote_recv(self):
        srv_id = int.from_bytes(self.data[:4], 4, 'big')
        srv = self.srv_list[srv_id]
    def send(self, command, data = None):
        self.cli.send(command)
        if isinstance(data, NoneType):
            self.cli.send(int.to_bytes(0, LEN, 'big'))
            return 0
        else:
            self.cli.send(int.to_bytes(len(data), LEN, 'big'))
            return self.cli.send(data)
    def recv(self):
        self.command = self.cli.recv(1)
        data_len = int.from_bytes(self.cli.recv(LEN), LEN, 'big')
        self.data = self.cli.recv(data_len)
    def close(self):
        self.send(QUIT)
        for srv_id in self.srv_list:
            srv = self.srv_list[srv_id]
            srv.close()
            #self.disconnect(srv_id)
        self.cli.close()
        raise BreakException()
class RemoteServer:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.srv = socket()
    def __call__(self):
        self.connect()
    def connect(self):
        self.srv.connect((self.addr, self.port))
    def send(self, msg):
        return self.srv.send(msg)
    def recv(self, len):
        return self.srv.recv(len)