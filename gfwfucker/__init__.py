"""
gfwfucker - A tool to bypass GFW!
"""
from struct                import Struct
from socket                import socket
from multiprocessing.dummy import Process

__author__ = 'cloudwindy'
__version__ = '1.0'

__all__ = ['GFWFucker']

# sender: client
# usage: keep connection alive
# data: none
# response: HEARTBEAT
HEARTBEAT  = b'\x00'

# sender: client
# usage: log in the server
# data: password's MD5
# response: CONNECT, status(boolean, False for success or True for failure)
HANDSHAKE  = b'\x01'

# sender: client
# usage: connect a server
# data: target IP and port
# response: status(boolean) and connection ID(int, an ID for a connection)
CONNECT    = b'\x02'

# sender: client
# usage: send messages to a connected server
# data: given connection ID and messages
# response: none
SEND       = b'\x03'

# sender: server
# usage: forward messages from a connected server
# data: given connection ID and messages
# response: none
RECV       = b'\x04'

# sender: client or server
# usage: disconnect a connected server
# data: given connection ID
# response: none
DISCONNECT = b'x05'

# sender: client
# usage: logout the server
# data: none
# response: a LOGOUT too
LOGOUT     = b'x06'

class GFWFucker:
    class BreakException:
        pass
    def __init__(self, addr, port, backlog):
        self.srv = socket()
        self.srv.bind((addr, port))
        self.srv.listen(backlog)
    def fuck(self):
        while True:
            cli = self.srv.accpet()
            Process(target = ClientHandler(cli))
class ClientHandler:
    def __init__(self, cli):
        self.cli = cli
    def __call__(self, cli):
        try:
            self.handshake()
            while True:
                self.recv()
                if self.command == HEARTBEAT:
                    self.heartbeat()
                elif self.command == HANDSHAKE:
                    self.handshake()
                elif self.command == CONNECT:
                    if self.is_logged = Ture:
                        self.connect()
                    else:
                        self.send()
        except BreakException:
            pass
        except Exception as e:
            print(repr(e))
            self.disconnect(cli)
    def send(self, command, data):
        self.srv.send(command)
        structer = Struct('i')
        data_len = structer.pack(len(data))
        self.send(data_len)
        self.send(data)
    def recv(self):
        self.command = self.cli.recv(1)
        structer = Struct('i')
        data_len = structer.unpack(self.cli.recv(4))[0]
        self.data = self.cli.recv(data_len)
