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

# usage: break
class BreakException(Exception):
    pass

# usage: main instance
class GFWFucker:
    def __init__(self, addr, port, password):
        self.srv = socket()
        self.srv.bind((addr, port))
        md5_obj = md5(SALT)
        md5_obj.update(password.encode())
        self.password = md5_obj.digest()
    def fuck(self):
        # fuck when you want
        self.srv.listen()
        pool = Pool(BACKLOG)
        while True:
            cli = self.srv.accept()
            cli_sock = cli[0]
            #cli_addr = '%s:%d' % cli[1]
            pool.apply_async(ClientHandler(cli_sock, self.password))
        pool.close()
        pool.join()

# usage: handle a client
class ClientHandler:
    def __init__(self, cli, password):
        self.srv = RemoteHandler()
        self.cli = cli
        self.password = password
    def __call__(self):
        try:
            self.handshake()
            while True:
                # mainloop
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
        port = int2bytes(self.data[4:8])
        try:
            srv_id = self.srv.new(addr, port)
        except Exception as e:
            self.send(FAILURE, repr(e))
        else:
            self.send(SUCCESS, srv_id)
    def remote_send(self):
        try:
            self.srv.send(self.data[4:])
        except Exception as e:
            self.send(FAILURE, repr(e))
    def remote_recv(self):
        self.srv.recv()
    def send(self, command, data = ''):
        self.cli.send(command)
        self.cli.send(int2bytes(len(data)))
        return self.cli.send(data)
    def recv(self):
        self.command = self.cli.recv(1)
        data_len = bytes2int(self.cli.recv(4))
        self.data = self.cli.recv(data_len)
    def close(self):
        raise BreakException()

# usage: handle clients' connections with remote server
class RemoteHandler:
    def __init__(self):
        self.srv_list = []
    def new(self, addr, port):
        self.srv_list += socket()
        self.srv_list[self.get_id()].connect((addr, port))
    def get_id(self):
        return len(self.srv_list) - 1
    def send(self, srv_id, msg):
        return self.srv_list[srv_id].send(msg)
    def recv(self, srv_id, len):
        return self.srv_list[srv_id].recv(len)
    def close(self, srv_id):
        self.srv_list[srv_id].close()
    def close_all(self):
        for srv in self.srv_list:
            srv.close()
# usage: change between int and bytes
def int2bytes(num):
    return int.to_bytes(num, 4, 'big')
def bytes2int(num):
    return int.from_bytes(num, 4, 'big')