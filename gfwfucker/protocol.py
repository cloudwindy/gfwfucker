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