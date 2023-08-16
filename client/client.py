from sock import *
import applications

import argparse

def main():
    parser = argparse.ArgumentParser(description='X11Forwarder')

    subparsers = parser.add_subparsers(dest='command')

    # Setup command creates a new server configuration file
    setup_parser = subparsers.add_parser('setup', help='Set up remote server')
    setup_parser.set_defaults(func=applications.setup_server_config)

    # List command lists all containers on the remote server
    list_parser = subparsers.add_parser('list', help='List remotes')
    list_parser.set_defaults(func=applications.list_remote_apps)
    
    # Launch command opens application via SSH
    launch_parser = subparsers.add_parser('launch', help='Launch remote application')
    launch_parser.add_argument('--id', required=True, help='ID of the remote')
    launch_parser.set_defaults(func=lambda args: applications.launch_remote_app(args.id))

    # Create command creates a new application on the server
    new_application_parser = subparsers.add_parser('create', help='Launches the tool to create a new remote application')
    new_application_parser.set_defaults(func=applications.new_remote_application)

    # Remove command deletes an application on the server
    remove_container = subparsers.add_parser('remove', help='Deletes a container')
    remove_container.add_argument('--id', required=True, help='ID of the remote')
    remove_container.set_defaults(func=lambda args: applications.remove_container(args.id))
    
    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()