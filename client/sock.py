import socket
import threading
import json

class TCPClient:
    def __init__(self, ip, port):
        """
        Initialize the TCP client that connects to the server 
        """
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """
        Connects to a server 
        """
        self.socket.connect((self.ip, self.port))

    def response(self):
        """
        Listens for a server response 
        """
        return self.socket.recv(1024).decode()

    def send(self, data):
        """
        Encodes & sends data to the server 
        """
        self.socket.send(data.encode())

    def close(self):
        """
        Closes the connection 
        """
        self.socket.close()