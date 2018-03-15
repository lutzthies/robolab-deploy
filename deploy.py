#!/usr/bin/env python3

"""
Deploy script that syncs files from the local 'src/' folder to a remote LEGO
MINDSTORMS EV3 brick running the customized operating system 'ev3dev-robolab'.
Aftwards it attaches to a pre-loaded tmux session running python3 including
some imported modules, performs a reload on the main.py file in the
/home/robot/src/ folder and starts execution from main.run().

For usage, optional arguments, syntax, et cetera please run this file with the
flag '--help', consult the README.md in the robolab-template repository or the
RoboLab Docs via the campus network of TU Dresden at
http://robolab.inf.tu-dresden.de

This module: https://github.com/7HAL32/robolab-deploy
It's usage as a submodule: https://github.com/7HAL32/robolab-template
The corresponding systemd service: https://github.com/7hAL32/ev3-robolab-startup

Part of the RoboLab project at TU Dresden.
Copyright (c) 2017 Lutz Thies
"""

import argparse
import os
import sys
import json
import shutil
import signal
import platform
import subprocess
import urllib.request
from getpass import getpass

# our imports
import tmuxify
from ip_check import ip_check

__author__ = 'Paul Genssler and Lutz Thies'
__copyright__ = 'Copyright (c) 2017'
__credits__ = [
               'Felix Döring',
               'Paul Genssler',
               'Lutz Thies',
               'Felix Wittwer',
               "Ian Alexander List"]

__license__ = 'MIT'
__version__ = '1.3.3'
__maintainer__ = 'Lutz Thies'
__email__ = 'lutz.thies@tu-dresden.de'
__status__ = 'Release'

# static global variables
ROBOLAB_SERVER = 'http://robolab.inf.tu-dresden.de/files/'
HOME = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(os.path.abspath(os.path.join(HOME, os.pardir)), 'src')
SETTINGS_PATH = os.path.join(HOME, '.bin', 'settings.json')
BIN_PATH = os.path.join(HOME, '.bin')
settings = dict()


class Windows:

    def __init__(self, settings):
        self.ip = settings['ip']
        self.password = settings['password']
        self.pscp = os.path.join(BIN_PATH, 'pscp.exe')
        self.putty = os.path.join(BIN_PATH, 'putty.exe')

        # check for the backup command
        self.backupfile = os.path.join(BIN_PATH, 'backup.txt')
        if not os.path.exists(self.backupfile):
            with open(self.backupfile, 'w') as new_backup:
                new_backup.write(raw_backup.format(''))

        # check the file containing the command that will be executed
        self.execfile = os.path.join(BIN_PATH, 'exec.txt')
        with open(self.execfile, 'w') as new_exec:
            new_exec.write(tmuxify.build_call(settings['password']))

    @staticmethod
    def backup():
        subprocess.call([os.path.join(BIN_PATH, 'putty.exe'), '-pw',
                         settings['password'], '-ssh',
                         'robot@{}'.format(settings['ip']), '-m',
                         os.path.join(BIN_PATH, 'backup.txt'), '-t'])
        print('Done')

    @staticmethod
    def copy_files():
        subprocess.call([os.path.join(BIN_PATH, 'pscp.exe'), '-pw',
                         settings['password'], '-r', SRC_PATH,
                         'robot@{ip}:/home/robot/'.format(ip=settings['ip'])])
        print('Done')

    @staticmethod
    def execute():
        subprocess.call([os.path.join(BIN_PATH, 'putty.exe'), '-pw',
                         settings['password'], '-ssh',
                         'robot@{}'.format(settings['ip']), '-m',
                         os.path.join(BIN_PATH, 'exec.txt'), '-t'])
        print('Done')

    @staticmethod
    def install():
        check_internet()
        pscp = os.path.join(BIN_PATH, 'pscp.exe')
        putty = os.path.join(BIN_PATH, 'putty.exe')

        # check for pscp
        if not os.path.exists(pscp):
            url = ROBOLAB_SERVER + 'pscp.exe'
            with urllib.request.urlopen(url) as download,\
                    open(pscp, 'wb') as file:
                file.write(download.read())

        # check for putty
        if not os.path.exists(putty):
            url = ROBOLAB_SERVER + 'putty.exe'
            with urllib.request.urlopen(url) as download,\
                    open(putty, 'wb') as file:
                file.write(download.read())


class Unix:

    def __init__(self, settings):
        self.ip = settings['ip']
        self.password = settings['password']

        # check for backup.sh
        self.backupfile = os.path.join(BIN_PATH, 'backup.sh')
        if not os.path.exists(self.backupfile):
            with open(self.backupfile, 'w') as new_backup:
                new_backup.write(raw_backup.format('#!/usr/bin/env bash\n\n'))

    @staticmethod
    def backup():
        with open(os.path.join(BIN_PATH, 'backup.sh'), 'r') as backupinput:
            subprocess.call([
                             'sshpass',
                             '-p',
                             settings['password'],
                             'ssh',
                             '-o',
                             'StrictHostKeyChecking=no',
                             'robot@{}'.format(settings['ip']),
                             'bash'
                             ],
                            stdin=backupinput
                            )
        print('Done')

    @staticmethod
    def copy_files():
        try:
            subprocess.call([
                             'sshpass',
                             '-p',
                             settings['password'],
                             'scp',
                             '-o',
                             'StrictHostKeyChecking=no',
                             '-r',
                             os.path.join(SRC_PATH),
                             'robot@{}:/home/robot/'.format(settings['ip'])
                             ])
        except OSError:
            Unix.install()
            Unix.copy_files()
        print('Done')

    @staticmethod
    def execute():
        subprocess.call(['sshpass', '-p', settings['password'],
                         'ssh','robot@{}'.format(settings['ip']), '-t',
                         tmuxify.build_call(settings['password'])])
        print('Done')

    @staticmethod
    def install():
        check_internet()
        # check for sshpass
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.call(['sshpass', '-V'], stdout=devnull)
        except FileNotFoundError:
            if "darwin" in sys.platform:
                try:
                    print('Installing sshpass')
                    with open(os.devnull, 'w') as devnull:
                        subprocess.call(
                            ['brew', 'install',
                             ROBOLAB_SERVER + 'sshpass.rb'],
                            stdout=devnull)
                except FileNotFoundError:
                    print(
                        'Failed\n\nYou have to install Homebrew first \
(http://brew.sh)')
                    sys.exit(1)
            else:
                pacmans = {
                    'yum': ['yum', 'install'],
                    'apt-get': ['apt-get', 'install'],
                    'pacman': ['pacman', '-S']
                        }
                pacman_found = False
                for pacman in pacmans.keys():
                    try:
                        with open(os.devnull, 'r') as devnull:
                            subprocess.call([pacmans[pacman][0], '-h'],
                                            stdout=devnull)
                        subprocess.call([
                                         'sudo',
                                         pacmans[pacman][0],
                                         pacmans[pacman][1],
                                         'sshpass'
                                        ])
                        pacman_found = True
                    except OSError:
                        continue
                if not pacman_found:
                    print("Your package manager was not found.")
                    print("Please manually install sshpass and rerun the deploy script")
                    sys.exit(1)




def main(copy=True, backup=False):
    # get the settings or create new ones
    global settings
    if not os.path.exists(SETTINGS_PATH):
        first_start()
    with open(SETTINGS_PATH) as s_file:
        settings = json.load(s_file)

    # get the platform specific routines
    print('Remembered OS is', settings['os'])
    system = Windows(settings) if settings['os'] == 'Windows' else Unix(settings)

    if backup:
        print('Backing up old files...')
        system.backup()

    if copy:
        print('Copying new files...')
        system.copy_files()

    print('Executing code by running main.run()')
    print('This will open a tmux session')
    print('Detach by pressing CTRL + B and then D')
    system.execute()


def check_internet():
    try:
        urllib.request.urlopen("http://google.com", timeout=1)
    except urllib.request.URLError:
        print("You will need to be connected to the internet!")
        print("Please ensure an internet connection to download")
        print("the essential tools and press Enter to proceed...")
        input()


def first_start():
    """
    Asks the user for necessary information and stores it
    """
    global settings
    Windows.install() if "win" in sys.platform else Unix.install()
    init_dict = dict()
    init_dict['os'] = platform.system()
    init_dict['ip'] = ip_check()
    init_dict['password'] = getpass('Enter the password of the "robot" user: ')
    # create paths and dump the data
    os.makedirs(os.path.join(BIN_PATH), exist_ok=True)
    with open(SETTINGS_PATH, 'w') as dump_file:
        json.dump(init_dict, dump_file, indent=4)


def abort(signal, frame):
    print('\rJob canceled by user!')
    sys.exit(0)


signal.signal(signal.SIGINT, abort)

raw_backup = '''{}if  [ ! -d ~/src ]
    then
    mkdir src
fi

if  [ ! -d ~/backup ]
    then
    mkdir backup
fi

cp -rf src backup
exit
'''


if __name__ == '__main__':
    os.chdir(HOME)
    print('RoboLab deploy script', 'v.' + __version__)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--configure',
        help='reset and create new configuration',
        action='store_true'
    )
    parser.add_argument(
        '-e',
        '--execute-only',
        help='do not copy files',
        action='store_false',
        default=True
    )
    parser.add_argument(
        '-b',
        '--backup',
        help='backup files on the brick',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '-U',
        '--update',
        help='Reload the robolab-deploy',
        action='store_true',
        default=False
    )
    args = parser.parse_args()

    print('If you need to change the IP address or password, please run\n\
      ./deploy.py -c')

    if not args.update:
        main(copy=args.execute_only, backup=args.backup)
    else:
        for file in os.listdir(os.getcwd()):
            filepath = os.path.join(os.getcwd(), file)
            if os.path.isfile(filepath):
                os.remove(filepath)
            else:
                shutil.rmtree(filepath)
        os.chdir(os.getcwd() + "/../")
        os.execv(
                 sys.executable,
                 ["python3"] + [(str(os.getcwd()) + "/deploy.py")]
        )

    if args.configure:
        first_start()
