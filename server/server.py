import socket
import threading

import os

import json
import applications
from configparser import ConfigParser

class TCPServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections = []

    def start(self):
        self.socket.bind((self.ip, self.port))

        self.socket.listen()
        print(f"Server listening on {self.ip}:{self.port}")

        while True:
            client_socket, client_address = self.socket.accept()
            print(f"Connection established with {client_address[0]}:{client_address[1]}")

            self.connections.append(client_socket)

            thread = threading.Thread(target=self.handle_connection, args=(client_socket,))
            thread.start()

    def handle_connection(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024).decode()

                if not data:
                    break

                data = json.loads(data)

                if data['action'] == 'create_new':
                    print('Building..')
                    
                    build_status = applications.create_container(name=data['name'], packages = [data['package']], exec=[data['exec']], persistent=data['persistent'])

                    client_socket.send(json.dumps(build_status).encode()) 

                    # Create a new configuration file for the app
                    config = ConfigParser()

                    config.add_section('Container')
                    config.set('Container', 'image_name', str(build_status['image_name']))
                    config.set('Container', 'volume_name', str(build_status['volume_name']))
                    config.set('Container', 'container_name', str(build_status['container_name']))
                    config.set('Container', 'image_id', str(build_status['image_id']))
                    config.set('Container', 'container_id', str(build_status['container_id']))
                    config.set('Container', 'persistent', str(build_status['persistent']))
                    config.set('Container', 'ssh_port', str(build_status['ssh_port']))

                    config_file = f"./config/{build_status['container_name']}.ini"
                    
                    with open(config_file, 'w') as file:
                        config.write(file)

                elif data['action'] == 'list':
                    config_files = os.listdir('./config')

                    configs = []

                    for filename in config_files:
                        if filename.endswith('.ini'):
                            config_file = f"./config/{filename}"

                            config = ConfigParser()
                            config.read(config_file)

                            container_info = {
                                'image_name': config.get('Container', 'image_name'),
                                'volume_name': config.get('Container', 'volume_name'),
                                'container_name': config.get('Container', 'container_name'),
                                'image_id': config.get('Container', 'image_id'),
                                'container_id': config.get('Container', 'container_id'),
                                'persistent': config.getboolean('Container', 'persistent'),
                                'ssh_port': config.get('Container', 'ssh_port')
                            }

                            configs.append(container_info)

                    client_socket.send(json.dumps({
                        'status': 'completed',
                        'configs': configs
                    }).encode())

                elif data['action'] == 'launch':    
                    client_socket.send(json.dumps(applications.start_container(data['container_id'])).encode())
                        
            except Exception as e:
                print(e)
                break

        client_socket.close()
        self.connections.remove(client_socket)

    def stop(self):
        for client_socket in self.connections:
            client_socket.close()

        self.server_socket.close()

# Perform checks before starting server 
if not os.path.isdir('config'):
    os.makedirs('config')
    
server = TCPServer('127.0.0.1', 8471)
server.start()
