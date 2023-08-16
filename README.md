
# X11Forwader

Access and manage applications running in a docker container remotely via SSH X11 forwarding. 


## Features

- List & transfer local applications 
- Create & remove custom docker images
- Launch a new window via SSH
- List remote applications

*Currently only supports Fedora systems*



## Usage/Examples

List all remote applications
```bash
$ python3 client.py list
```

Create a new application. Building images can take some time.
```bash
$ python3 ./client/client.py create
Please select one of the following options to create a new application: 
1) List local applications to transfer
2) Configure a new remote application
Please enter your selection> 2
Please enter the name of the package to install> firefox
Suggested package: firefox.x86_64
Please enter the package you would like to install (Press enter to use suggested)> 
Please enter the command to launch the application (Press enter to use package name)> 
Enter the name of the container> Browser            
Do you want the container to be persistent?> 
Using server with IP localhost and port 8471
Building app...
Container browser_4660343961 created successfully. Details:
Image name:browser_4660343961
Volume name:None
Container name:browser_4660343961
Image ID:sha256:eb8f74af78cd0ad69731a8501fd7b1cd00c03443f3bb9324b2e9237af7ebe7b3
Container ID:53c4276f74b5baf093bf3943143fa8f26952a8e5b5378f38b20595d967665255
Persistent:False
```

Remove a container
```bash
$ python3 client.py --id <container_id>
```
Launch a container
```bash
$ python3 client.py launch --id <container_id>
```


## Run Locally

Make sure [Docker](https://docs.docker.com/engine/install/) is installed. 

Clone the github repository 
```bash
git clone https://github.com/TimidFuzz/X11Forwarder.git
```

Launch the server. Make sure docker is installed and the firewall is not blocking any ports.
```bash
cd X11Forwarder/server/
python3 server.py
```

Using the client cli tool
```bash
cd X11Forwarder/client/
python3 client.py -h

usage: client.py [-h] {setup,list,launch,create,remove} ...

positional arguments:
  {setup,list,launch,create,remove}
    setup               Set up remote server
    list                List remotes
    launch              Launch remote application
    create              Launches the wizzard to create a new remote application
    remove              Deletes a container

options:
  -h, --help            show this help message and exit
```


## Contributing

Contributions are always welcome!

[@TimidFuzz](https://github.com/TimidFuzz/)