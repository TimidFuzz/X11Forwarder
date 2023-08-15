import docker
import os 

import random

client = docker.from_env()

def build_docker_container(image_name, packages, exec):
    dockerfile_path = os.path.expanduser('~/.remote_apps/config/Dockerfile')
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

RUN echo 'root:password' | chpasswd
''')

    try:
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

def create_container(name, packages, exec, persistent):
    name = name.replace(' ', ('_')).lower()
    name = f'{name}_{"".join([str(random.randint(0, 9)) for i in range(10)])}'

    try:
        output = build_docker_container(name, packages, exec)
        
        if output['status'] == 'failed':
            return output
        
        if persistent == True:
            client.volumes.create(name)

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

import time

def start_container(container_id):
    try:
        container = client.containers.get(container_id)

        if container:
            container.start()

            while container.status != 'running':
                time.sleep(1)
                container.reload()

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