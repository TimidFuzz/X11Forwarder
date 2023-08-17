import docker
import os 

import random

from configparser import ConfigParser
import time

client = docker.from_env()

def list_apps():
    """
    List all apps from configuration files
    """
    configs = []

    # Loop through the files in the directory and read the configuration files
    for filename in os.listdir('./config'):
        if filename != 'server.ini' and filename.endswith('.ini'):
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

    return {
        'status': 'completed',
        'configs': configs
    }


def remove_application(container_id):
    """
    Remove the container, image and configuration file
    """
    try:
        # Fetch & Delete docker container 
        container = client.containers.get(container_id)
        container.stop()
        container.remove()

        # Delete the docker image
        image_id = container.image.id

        client.images.remove(image_id, force=True)
        
        # Delete the configuration file
        for file in os.listdir('./config'):
            if file.endswith('.ini') and file != 'server.ini' :
                config_file = f'./config/{file}'

                config = ConfigParser()
                config.read(config_file)

                if config.get('Container', 'container_id') == container_id:
                    os.remove(config_file)
                    
                    return {
                        'status': 'completed'
                    }
        
    except Exception as e:
        return {
            'status': 'failed',
            'error': f'{e}'
        }

def build_docker_image(image_name, packages, exec, password):
    """
    Build a docker omage based on the packages to install
    """
    dockerfile_path = os.path.expanduser('~/.remote_apps/config/Dockerfile')
    
    # Write the Dockerfile to a file temporarily
    with open(dockerfile_path, 'w') as file:
        file.write(f'''
FROM fedora:latest

RUN dnf -y update && \\
    dnf -y install {" ".join(packages)} openssh-server xorg-x11-server-Xvfb

RUN ssh-keygen -A

RUN echo "X11Forwarding yes" >> /etc/ssh/sshd_config && \\
    echo "X11UseLocalhost no" >> /etc/ssh/sshd_config && \\
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config

RUN mkdir -p /root/.ssh && \\
    touch /root/.Xauthority

RUN chmod 600 /root/.ssh && \\
    chmod 600 /root/.Xauthority

RUN echo '{"&&".join(exec)} && exit &' >> /root/.bashrc

EXPOSE 22

CMD /usr/sbin/sshd && Xvfb :1 -screen 0 1024x768x16
ENV DISPLAY=:1

RUN echo 'root:{password}' | chpasswd
''')

    try:
        # Build the image
        client.images.build(path=os.path.expanduser('~/.remote_apps/config'), tag=image_name)

        image_id = client.images.get(image_name).attrs['Id']
        
        return {
            'status': 'completed',
            'id': image_id
        }
    except docker.errors.BuildError as e:
        return {
            'status': 'failed',
            'error': f"Failed to build Docker container. Error: {e}"
        }
    except Exception as e:
        return {
            'status': 'failed',
            'error': f"Failed to build Docker container. Error: {e}"
        }

def create_config(image_name, volume_name, container_name, image_id, container_id, persistent, ssh_port):
    """
    Creates a new configuration file
    """
    config = ConfigParser()

    config.add_section('Container')
    config.set('Container', 'image_name', image_name)
    config.set('Container', 'volume_name', volume_name)
    config.set('Container', 'container_name', container_name)
    config.set('Container', 'image_id', image_id)
    config.set('Container', 'container_id', container_id)
    config.set('Container', 'persistent', persistent)
    config.set('Container', 'ssh_port', ssh_port)

    config_file = f'./config/{container_name}.ini'
                    
    with open(config_file, 'w') as file:
        config.write(file)

def create_container(name, packages, exec, persistent, password):
    """
    Create a new container for the app 
    """
    # Generate new unique container_name
    name = name.replace(' ', ('_')).lower()
    name = f'{name}_{"".join([str(random.randint(0, 9)) for i in range(10)])}'

    try:
        # Build the image
        output = build_docker_image(name, packages, exec, password)
        
        if output['status'] == 'failed':
            return output
        
        # Create a new volume that can be attached for permanent storage
        if persistent == True:
            client.volumes.create(name)
        
        # Find a port that will be exposed on the host system
        host_port = random.randint(1024, 65535)
        
        container = client.containers.create(
            image=output['id'],
            name=name,
            ports={22: host_port},
            volumes={f'{name}': {'bind': '/home', 'mode': 'rw'}},
        ) if persistent == True else client.containers.create(
            image=output['id'],
            name=name,
            ports={22: host_port},
            )
        
        return {
            'status': 'completed',
            'image_name': name,
            'volume_name': name if persistent == True else None,
            'container_name': name,
            'image_id': output['id'],
            'container_id': container.id,
            'persistent': persistent,
            'ssh_port': host_port
        }
    
    except docker.errors.APIError as e:
        return {
            'status': 'failed',
            'error': f"An issue with the API has occured. Error: {e}"
        }
    except Exception as e:
        return {
            'status': 'failed',
            'error': f"An error occurred during container creation. Error: {e}"
        }

def start_container(container_id):
    """
    Launches a new instance of the container
    """
    try:
        # Fetch container
        container = client.containers.get(container_id)

        if container:
            container.start()

            while container.status != 'running':
                time.sleep(1)
                container.reload()
            
            # Fetch exposed port on host for ssh
            ports = container.attrs['NetworkSettings']['Ports']['22/tcp'][0]['HostPort']

            response = {
                'status': 'success',
                'ports': ports
            }

            if container.status == 'running':
                response['warning'] = f'Container {container_id} is already running'

            return response
        else:
            return {
                'status': 'failed',
                'error': f"Container '{container_id}' does not exist."
            }
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }