import hashlib

import re

import os
import subprocess
from configparser import ConfigParser

import utils
import sock
import json

def check_config():
    pass

def get_server():
    server_config = ConfigParser()

    server_config.read(os.path.expanduser('~/.remote_apps/config/server.ini'))
    
    IP = server_config.get('Server', 'ip')
    PORT = server_config.get('Server', 'port')
    
    PORT = int(PORT) if type(PORT) == str else PORT

    return IP, PORT
    
def list_remote_apps(args):
    server_ip, server_port = get_server()

    print(f'Using server with IP {server_ip} and port {server_port}')
    print('Fetching list of remote apps')

    socket = sock.TCPClient(server_ip, server_port)
    socket.connect()   

    message = {
        'action': 'list'
    }

    socket.send(json.dumps(message))

    response = json.loads(socket.response())

    if response['status'] == 'completed':
        print('======= Remote applications =======')
        
        for config in response['configs']:
            print(f'Image Name: {config["image_name"]}')
            print(f'Volume Name: {config["volume_name"]}')
            print(f'Container Name: {config["container_name"]}')
            print(f'Image ID: {config["image_id"]}')
            print(f'Container ID: {config["container_id"]}')
            print(f'Persistent: {config["persistent"]}')
            print(f'SSH port: {config["ssh_port"]}')
            print('---')

def remove_container(container_id):
    server_ip, server_port = get_server()

    socket = sock.TCPClient(server_ip, server_port)
    socket.connect()   

    message = {
        'action': 'remove',
        'container_id' : container_id
    }

    socket.send(json.dumps(message))
    
    response = socket.response()
    response = json.loads(response)

    if response['status'] == 'completed':
        print(f'Deleted {container_id} successfully')
    elif response['status'] == 'failed':
        print(response['error'])

def launch_remote_app(identifier):
    server_ip, server_port = get_server()

    socket = sock.TCPClient(server_ip, server_port)
    socket.connect()   

    message = {
        'action': 'launch',
        'container_id' : identifier
    }

    socket.send(json.dumps(message))
    
    response = socket.response()
    response = json.loads(response)

    if response['status'] == 'success':
        port = response['ports']
        username = 'root'
        password = 'password'

        if 'warning' in response:
            print(response['warning'])

        ssh_command = f'sshpass -p {password} ssh -X -p {port} -o StrictHostKeyChecking=no {username}@{server_ip}'

        subprocess.run(ssh_command, shell=True)

    elif response['status'] == 'failed':
        print(f'An error occured. {response["error"]}')
    else:
        print('An unknown error occured')

def list_local_applications():
    applications = [re.search(r'([^/]+)\.desktop$', app).group(1) for app in utils.get_desktop_apps()]
    applications = [re.sub(r'org', '', app) for app in applications]
    applications = [app.replace('.', '-') for app in applications]
    applications = [app.strip() for app in applications] 
    
    applications = "\n".join(applications)

    print('========== List of applications ==========')
    print(applications)

def new_remote_application(args):
    print('Please select one of the following options to create a new application: ')
    print('1) List local applications to transfer')
    print('2) Configure a new remote application')

    choice = input('Please enter your selection> ')

    while True:
        if choice == '1':
            list_local_applications()
        
        if choice == '1' or choice == '2':
            choice = input('Please enter the name of the package to install> ')
            suggestion = utils.search_package(choice)

            if not suggestion:
                print('No suggestion')
            else:
                print(f'Suggested package: {suggestion}')

            package_to_install = input('Please enter the package you would like to install (Press enter to use suggested)> ')

            if not package_to_install:
                package_to_install = suggestion
            
            exec_command = input('Please enter the command to launch the application (Press enter to use suggested)> ')

            if not exec_command:
                exec_command = choice

            container_name = input('Enter the name of the container (Press enter to use suggested)> ')

            if not container_name:
                container_name = choice
            
            container_persistent = True if 'yes' == input('Do you want the container to be persistent? (Press enter to use suggested)> ').lower() else False
            
            # Choose server
            server_ip, server_port = get_server()

            print(f'Using server with IP {server_ip} and port {server_port}')
            print('Building app...')

            socket = sock.TCPClient(server_ip, server_port)
            socket.connect()   

            message = {
                'action': 'create_new',
                'name': container_name,
                'package': package_to_install,
                'exec': exec_command,
                'persistent': container_persistent
            }

            socket.send(json.dumps(message))

            response = json.loads(socket.response())

            if response['status'] == 'sucess' or response['status'] == 'completed':
                print(f'Container {response["container_name"]} created successfully. Details:\nImage name:{response["image_name"]}\nVolume name:{response["volume_name"]}\nContainer name:{response["container_name"]}\nImage ID:{response["image_id"]}\nContainer ID:{response["container_id"]}\nPersistent:{response["persistent"]}')

            elif response['status'] == 'failed':
                print(response['error'])

            else:
                print(f'An unknown error occured')

            return

def setup_server_config(args):
    if not os.path.exists(os.path.expanduser('~/.remote_apps/config')):
        print('First time running...')
        print('Creating necessary configuartion files...')

        os.makedirs(os.path.expanduser('~/.remote_apps/config/'))

        print('No configuration file. Please answer the following questions to create one')
        
        server_name = input("Enter server name: ")
        server_ip = input("Enter server IP address: ")
        server_port = input("Enter port number: ")
        username = input("Enter username for authentication (Leave empty if no authentication is set up): ")
        password = input("Enter password for authentication (Leave empty if no authentication is set up): ")

        hash = hashlib.md5()
        hash.update(password.encode('utf-8'))
        hash = hash.hexdigest()

        config = ConfigParser()

        config.add_section('Server')
        config.set('Server', 'Name', server_name)
        config.set('Server', 'IP', server_ip)
        config.set('Server', 'Port', server_port)
        config.set('Server', 'Username', username)
        config.set('Server', 'Password', hash)

        config_file = os.path.expanduser('~/.remote_apps/config/server.ini')
        with open(config_file, 'w') as file:
            config.write(file)

        print("Server configuration created successfully!")

    else:
        print('Delete the directory ~/.remote_apps/config first')