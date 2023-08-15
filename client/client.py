from sock import *
import applications

import argparse

def main():
    parser = argparse.ArgumentParser(description='Remote Apps')

    subparsers = parser.add_subparsers(dest='command')

    setup_parser = subparsers.add_parser('setup', help='Set up remote server')
    setup_parser.set_defaults(func=applications.setup_server_config)

    list_parser = subparsers.add_parser('list', help='List remotes')
    list_parser.set_defaults(func=applications.list_remote_apps)

    launch_parser = subparsers.add_parser('launch', help='Launch remote application')
    launch_parser.add_argument('--id', required=True, help='ID of the remote')
    launch_parser.set_defaults(func=lambda args: applications.launch_remote_app(args.id))

    new_application_parser = subparsers.add_parser('create', help='Launches the wizzard to create a new remote application')
    new_application_parser.set_defaults(func=applications.new_remote_application)
    
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