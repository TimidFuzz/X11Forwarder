import socket
import threading
import json

class TCPClient:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect((self.ip, self.port))

    def response(self):
        return self.socket.recv(1024).decode()

    def send(self, data):
        self.socket.send(data.encode())

    def close(self):
        self.socket.close()


def authenticateClient(ip, port):
    pass

def sendOpenContainer(ip, port, username, hash, containerId):
    socket = TCPClient(ip, port)
    socket.connect()
    
    message = {
        'id': containerId,
        'username': username,
         'creds': hash
    } if hash and username else {
        'id': containerId
    }

    socket.send(json.dumps(message).encode())
    
def sendCreateNewContainer(ip, port, package):
    port = int(port) if isinstance(port, str) else port

    socket = TCPClient(ip, port)
    socket.connect()

    message = {
        'action': 'create_new',
        'package': package
    }

    socket.send(json.dumps(message))

    return socket.response()