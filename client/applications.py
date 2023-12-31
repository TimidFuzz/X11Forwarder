import hashlib

import re

import os
import subprocess
from configparser import ConfigParser

import utils
import sock
import json

def get_server():
    """
    Retrieve server IP and port from configuration file
    """
    server_config = ConfigParser()

    server_config.read(os.path.expanduser('~/.remote_apps/config/server.ini'))
    
    IP = server_config.get('Server', 'ip')
    PORT = server_config.get('Server', 'port')
    password = server_config.get('Server', 'password')
    
    PORT = int(PORT) if type(PORT) == str else PORT

    return IP, PORT, password
    
def list_remote_apps(args):
    """
    Lists all remote applications on the server
    """
    server_ip, server_port, password = get_server()

    print(f'Using server with IP {server_ip} and port {server_port}')
    print('Fetching list of remote apps')

    # Establishes a new connection
    socket = sock.TCPClient(server_ip, server_port, password)
    socket.connect()   

    message = {
        'action': 'list'
    }
    
    # Sends the command 
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
    """
    Removes a remote container
    """
    server_ip, server_port, password = get_server()

    # Establishes a connection
    socket = sock.TCPClient(server_ip, server_port, password)
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
    """
    Retrieves the ssh port of the container and launches a new instance via SSH
    """
    server_ip, server_port, password = get_server()

    # Establishes a new connection
    socket = sock.TCPClient(server_ip, server_port, password)
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

        if 'warning' in response:
            print(response['warning'])

        # SSH into remote container
        ssh_command = f'sshpass -p {password} ssh -X -p {port} -o StrictHostKeyChecking=no {username}@{server_ip}'

        subprocess.run(ssh_command, shell=True)

    elif response['status'] == 'failed':
        print(f'An error occured. {response["error"]}')
    else:
        print('An unknown error occured')

def list_local_applications():
    """
    Extract the installed applications from the desktop files
    """
    applications = [re.search(r'([^/]+)\.desktop$', app).group(1) for app in utils.get_desktop_apps()]
    applications = [re.sub(r'org', '', app) for app in applications]
    applications = [app.replace('.', '-') for app in applications]
    applications = [app.strip() for app in applications] 
    
    applications = "\n".join(applications)

    print('========== List of applications ==========')
    print(applications)

def new_remote_application(args):
    """
    Initiates the creation of a new remote application
    """
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

            # Choose the package to be installed
            package_to_install = input('Please enter the package you would like to install (Press enter to use suggested)> ')

            if not package_to_install:
                package_to_install = suggestion
            
            # Choose the command that will be used to launch the application e.g libreoffice --writer
            exec_command = input('Please enter the command to launch the application (Press enter to use suggested)> ')
            
            if not exec_command:
                exec_command = choice

            # Choose the name of the container
            container_name = input('Enter the name of the container (Press enter to use suggested)> ')
            
            if not container_name:
                container_name = choice
            
            # Choose whether container should be persistent (volume will be mounted)
            container_persistent = True if 'yes' == input('Do you want the container to be persistent? (Press enter to use suggested)> ').lower() else False
            
            # Choose server
            server_ip, server_port, password = get_server()

            print(f'Using server with IP {server_ip} and port {server_port}')
            print('Building app. This may take a while...')

            # Establish a new connection
            socket = sock.TCPClient(server_ip, server_port, password)
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
    """
    Creates a server configuration file 
    """
    if not os.path.exists(os.path.expanduser('~/.remote_apps/config')):
        print('First time running...')
        print('Creating necessary configuartion files...')

        os.makedirs(os.path.expanduser('~/.remote_apps/config/'))

        print('No configuration file. Please answer the following questions to create one')
        
        server_name = input('Enter server name: ')
        server_ip = input('Enter server IP address: ')
        server_port = input('Enter port number: ')
        password = input('Enter password for authentication (Leave empty if no authentication is set up): ')

        hash = hashlib.md5()
        hash.update(password.encode('utf-8'))
        hash = hash.hexdigest()

        config = ConfigParser()

        config.add_section('Server')
        config.set('Server', 'Name', server_name)
        config.set('Server', 'IP', server_ip)
        config.set('Server', 'Port', server_port)
        config.set('Server', 'Password', hash)

        config_file = os.path.expanduser('~/.remote_apps/config/server.ini')
        with open(config_file, 'w') as file:
            config.write(file)

        print('Server configuration created successfully!')

    else:
        print('Delete the directory ~/.remote_apps/config first')