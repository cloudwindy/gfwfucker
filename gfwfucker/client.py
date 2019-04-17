from gfwfucker.base import BaseHandler, BaseForwarder
from gfwfucker.protocol import HANDSHAKE, FAILURE
from gfwfucker.tools import md5
from socket   import inet_ntoa

__all__ = ['GFWFuckerHTTPLocal', 'GFWFuckerSOCKSLocal', 'GFWFuckerClient']

class GFWFuckerHTTPLocal(BaseHandler, BaseForwarder):
    """
    local - client - server - remote
          ^ HTTP local handler
    """
    def __init__(self, reader, writer):
        BaseHandler.__init__(self, reader, writer)
        BaseForwarder.__init__(self, self._forward)
    def _forward(self, data):
        pass
class GFWFuckerSOCKSLocal(BaseHandler, BaseForwarder):
    """
    local - client - server - remote
          ^ SOCKS local handler
    """
    def __init__(self, reader, writer):
        BaseHandler.__init__(self, reader, writer)
        BaseForwarder.__init__(self, self._forward)
    def _forward(self, data):
        pass
class GFWFuckerClient(BaseHandler):
    """
    local - client - server - remote
                   ^ connect handler
    """
    def __init__(self, addr, port, password):
        BaseHandler.__init__(self, addr, port)
        self.is_verified = False
        self.send_pack(HANDSHAKE, md5(password))
        self.recv_pack()
        if self.command == FAILURE:
            self.c('Handshake failed! Reason: ' + self.data.encode())
    def handle_read(self):
        self.recv_pack()
    def forward(self):
        pass