import subprocess

import hashlib

import os

import glob
from configparser import ConfigParser

def parse_desktop_file(file_path):
    config = ConfigParser()
    config.read(file_path)
    return config.get('Desktop Entry', 'Name')

def get_installed_packages():
    return subprocess.check_output(['rpm', '-qa']).decode('utf-8').split('\n')[:-1]

def get_desktop_apps():
    return glob.glob('/usr/share/applications/*.desktop')


def search_package(package_name):
    command = ['dnf', 'search', package_name]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        output_lines = result.stdout.strip().split('\n')
        if len(output_lines) > 1:
            columns = output_lines[1].split()

            best_match = columns[0]
            return best_match

    return None