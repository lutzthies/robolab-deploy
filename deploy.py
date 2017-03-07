#!/usr/bin/python3

'''
Deploy script that syncs files from the local 'src/' folder to a remote LEGO
MINDSTORMS EV3 brick running the customized operating system 'ev3dev-robolab'.
Aftwards it attaches to a pre-loaded tmux session running python3 including
some imported modules, performs a reload on the main.py file in the
/home/robot/src/ folder and starts execution from main.run()

For usage, optional arguments, syntax, et cetera please run this file with the
flag '--help'.

This module: https://github.com/7HAL32/robolab-deploy
The corresponding systemd service: https://github.com/7hAL32/ev3-robolab-startup

Developed as a part of the RoboLab project at TU Dresden.
(c) 2017 Lutz Thies
'''
import argparse
import os
import sys
import json
import signal
import platform
import subprocess
import urllib.request
import distutils.dir_util
from ip_check import *

__author__ = 'Paul Genssler and Lutz Thies'
__copyright__ = 'Copyright (c) 2017'
__credits__ = ['Felix Döring', 'Paul Genssler', 'Lutz Thies', 'Felix Wittwer']

__license__ = 'MIT'
__version__ = '1.2.0'
__maintainer__ = 'Lutz Thies'
__email__ = 'lutz.thies@tu-dresden.de'
__status__ = 'Release'

home = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(os.path.abspath(os.path.join(home, os.pardir)), 'src')
settings_path = os.path.join(home, '.bin', 'settings.json')
bin_path = os.path.join(home, '.bin')
settings = dict()

# the command that reloads the python modules in tmux and attaches to the
# session afterwards
tmux_command = 'tmux -S /tmp/tmux/shared send -t ev3-robolab-startup \
"reloader.enable(blacklist=[\'ev3dev\',\'ev3dev.ev3\',\'ev3\',\'typing\'])" ENTER \
"reloader.reload(main)" ENTER \
"main.run()" ENTER; \
tmux -S /tmp/tmux/shared attach -t ev3-robolab-startup'

class Windows:

    def __init__(self, settings):
        self.ip = settings['ip']
        self.password = settings['password']
        self.pscp = os.path.join(bin_path, 'pscp.exe')
        self.putty = os.path.join(bin_path, 'putty.exe')

        # check for pscp
        if not os.path.exists(self.pscp):
            url = 'http://robolab.inf.tu-dresden.de/files/pscp.exe'
            with urllib.request.urlopen(url) as download,\
                    open(self.pscp, 'wb') as file:
                file.write(download.read())

        # check for putty
        if not os.path.exists(self.putty):
            url = 'http://robolab.inf.tu-dresden.de/files/putty.exe'
            with urllib.request.urlopen(url) as download,\
                    open(self.putty, 'wb') as file:
                file.write(download.read())

        # check for the backup command
        self.backupfile = os.path.join(bin_path, 'backup.txt')
        if not os.path.exists(self.backupfile):
            with open(self.backupfile, 'w') as new_backup:
                new_backup.write(raw_backup.format(''))

        # check the file containing the command that will be executed
        self.execfile = os.path.join(bin_path, 'exec.txt')
        with open(self.execfile, 'w') as new_exec:
            new_exec.write(tmux_command)

    @staticmethod
    def backup():
        subprocess.call([os.path.join(bin_path, 'putty.exe'), '-pw',
                         settings['password'], '-ssh',
                         'robot@{}'.format(settings['ip']), '-m',
                         os.path.join(bin_path, 'backup.txt'), '-t'])
        print('Done')

    @staticmethod
    def copy_files():
        subprocess.call([os.path.join(bin_path, 'pscp.exe'), '-pw',
                         settings['password'], '-r', src_path,
                         'robot@{ip}:/home/robot/'.format(ip=settings['ip'])])
        print('Done')

    @staticmethod
    def execute():
        subprocess.call([os.path.join(bin_path, 'putty.exe'), '-pw',
                         settings['password'], '-ssh',
                         'robot@{}'.format(settings['ip']), '-m',
                         os.path.join(bin_path, 'exec.txt'), '-t'])
        print('Done')

class Unix:

    def __init__(self, settings):
        self.ip = settings['ip']
        self.password = settings['password']
        # check for backup.sh
        self.backupfile = os.path.join(bin_path, 'backup.sh')
        if not os.path.exists(self.backupfile):
            with open(self.backupfile, 'w') as new_backup:
                new_backup.write(raw_backup.format('#!/usr/bin/env bash\n\n'))
        # check for sshpass
        try:
            with open(os.devnull, 'w') as devnull:
                subprocess.call(['sshpass', '-V'], stdout=devnull)
        except FileNotFoundError:
            if settings['os'] == 'Darwin':
                try:
                    print('Installing sshpass')
                    with open(os.devnull, 'w') as devnull:
                        subprocess.call(
                            ['brew', 'install',
                             'http://141.76.44.173/files/sshpass.rb'],
                            stdout=devnull)
                except FileNotFoundError:
                    print(
                        'Failed\n\nYou have to install Homebrew first \
(http://brew.sh)')
                    sys.exit(1)
            else:
                print('''Please install sshpass

with apt-get:
sudo apt-get install sshpass

Further information:
https://gist.github.com/arunoda/7790979''')
                sys.exit(1)

    @staticmethod
    def backup():
        with open(os.path.join(bin_path, 'backup.sh'), 'r') as backupinput:
            subprocess.call(['sshpass', '-p', settings['password'], 'ssh', '-o',
                             'StrictHostKeyChecking=no', 'robot@{}'.format(
                             settings['ip']), 'bash'],
                            stdin=backupinput)
        print('Done')

    @staticmethod
    def copy_files():
        subprocess.call(['sshpass', '-p', settings['password'], 'scp', '-o',
                         'StrictHostKeyChecking=no', '-r',
                         os.path.join(src_path),
                         'robot@{}:/home/robot/'.format(
            settings['ip'])])
        print('Done')

    @staticmethod
    def execute():
        # command = "; ".join((backup_command, tmux_command))
        command = tmux_command
        subprocess.call(['sshpass', '-p', settings['password'],
                         'ssh','robot@{}'.format(settings['ip']), '-t', command])
        print('Done')


def main(copy=True, backup=False):
    # get the settings or create new ones
    global settings
    if not os.path.exists(settings_path):
        first_start()
    with open(settings_path) as file:
        settings = json.load(file)

    # get the platform specific routines
    print('Remembered OS is', settings['os'])
    system = Windows(settings) if settings['os'] == 'Windows' else Unix(settings)

    if backup:
        print('INFO - Backing up old files...')
        system.backup()

    if copy:
        print('INFO - Copying new files...')
        system.copy_files()

    print('INFO - Executing code by running main.run()')
    print('INFO - This will open a tmux session')
    print('INFO - Dettach by pressing CTRL + B and then D')
    system.execute()


def first_start():
    '''
    Asks the user for necessary information and stores it
    '''
    init_dict = dict()
    init_dict['os'] = platform.system()
    init_dict['ip'] = ip_check()
    init_dict['password'] = input('Please enter the robots password: ')
    # create paths and dump the data
    os.makedirs(os.path.join(bin_path), exist_ok=True)
    with open(settings_path, 'w') as dump_file:
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
    print('RoboLab deploy script', 'v.' + __version__)
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--configure', help='reset and create new configuration',  action='store_true')
    parser.add_argument(
        '-e', '--execute-only', help='do not copy files', action='store_false', default=True)
    parser.add_argument(
        '-b', '--backup', help='backup files on the brick', action='store_true', default=False)
    args = parser.parse_args()

    print('INFO: If you have to change the IP or password, run\n\
      ./deploy.py -n')

    if args.configure:
        first_start()
    main(copy=args.execute_only, backup=args.backup)
