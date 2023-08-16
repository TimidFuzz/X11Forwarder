import socket
import threading

import os

import json
import applications
from configparser import ConfigParser
import argparse

# Configuration
parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8080,
                        help='The port to listen on')
parser.add_argument('--ip', type=str, default='127.0.0.1',
                        help='The server IP')

args = parser.parse_args()

class TCPServer:
    def __init__(self, ip, port):
        """
        Initialize the TCP server that handles client connections
        """
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []

    def start(self):
        """
        Start listening for client connections
        """
        self.socket.bind((self.ip, self.port))

        self.socket.listen()

        print(f'Server listening on {self.ip}:{self.port}')

        while True:
            client_socket, client_address = self.socket.accept()

            print(f'Connection established with {client_address[0]}:{client_address[1]}')

            self.connections.append(client_socket)

            thread = threading.Thread(target=self.handle_connection, args=(client_socket,))
            thread.start()

    def handle_connection(self, client_socket):
        """
        Handle client connections and listen for packets
        """
        while True:
            try:
                data = client_socket.recv(1024).decode()

                if not data:
                    break

                data = json.loads(data)

                if data['action'] == 'create_new':           
                    # Build the image         
                    build_status = applications.create_container(name=data['name'], packages = [data['package']], exec=[data['exec']], persistent=data['persistent'])

                    # Create a new configuration file
                    applications.create_config(image_name=str(build_status['image_name']), volume_name=str(build_status['volume_name']), container_name=str(build_status['container_name']), image_id=str(build_status['image_id']), container_id=str(build_status['container_id']), persistent=str(build_status['persistent']), ssh_port=str(build_status['ssh_port']))

                    # Send the Information about the new container
                    client_socket.send(json.dumps(build_status).encode()) 
                
                elif data['action'] == 'list':
                    # List all apps
                    configs = applications.list_apps()

                    # Send the List
                    client_socket.send(json.dumps(configs).encode())

                elif data['action'] == 'launch':    
                    # Launch the container
                    response = applications.start_container(data['container_id'])

                    # Return information on the status of the command
                    client_socket.send(json.dumps(response).encode())

                elif data['action'] == 'remove':    
                    # Remove the application
                    response = applications.remove_application(data['container_id'])
                    
                    # Return information on the status of the command
                    client_socket.send(json.dumps(response).encode())

            except Exception as e:
                print(f'An error occured: {e}')
                break

        client_socket.close()
        self.connections.remove(client_socket)

    def stop(self):
        """
        Close server & all outgoing client connections
        """
        for client_socket in self.connections:
            client_socket.close()

        self.server_socket.close()

# Perform checks before starting server 
if not os.path.isdir('config'):
    os.makedirs('config')

server = TCPServer(args.ip, args.port)
server.start()
