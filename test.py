#!/usr/bin/python3

"""

"""

import os
import sys
import json
import signal
import platform
import subprocess
import urllib.request
import distutils.dir_util
from ip_check import *

__author__ = "Lutz Thies"
__copyright__ = "Copyright (c) 2017"
__credits__ = ["Felix Döring", "Felix Wittwer", "Lutz Thies"]

__license__ = "MIT"
__version__ = "1.2.0"
__maintainer__ = "Lutz Thies"
__email__ = "lutz.thies@tu-dresden.de"
__status__ = "Pre-Release"

home = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(os.path.abspath(os.path.join(home, os.pardir)), 'src/')
backup_path = os.path.join(home, '.backup')
settings_path = os.path.join(home, '.bin', 'settings.json')
bin_path = os.path.join(home, '.bin')
settings = dict()

tmux_command = 'tmux -S /tmp/tmux/shared send -t ev3-robolab-startup "reloader.reload(main)" ENTER "main.run()" ENTER; tmux -S /tmp/tmux/shared attach -t ev3-robolab-startup'

class Windows:

    def __init__(self, settings):
        self.ip = settings['ip']
        self.password = settings['password']
        self.pscp = os.path.join(bin_path, 'pscp.exe')
        self.putty = os.path.join(bin_path, 'putty.exe')

        # Download Putty and pscp if they do not exist
        if not os.path.exists(self.pscp):
            url = 'http://141.76.44.173/files/pscp.exe'
            with urllib.request.urlopen(url) as download,\
                    open(self.pscp, 'wb') as file:
                file.write(download.read())
        if not os.path.exists(self.putty):
            url = 'http://141.76.44.173/files/putty.exe'
            with urllib.request.urlopen(url) as download,\
                    open(self.putty, 'wb') as file:
                file.write(download.read())

        # Check for backup.txt
        self.backupfile = os.path.join(bin_path, 'backup.txt')
        self.execfile = os.path.join(bin_path, 'exec.txt')
        if not os.path.exists(self.backupfile):
            with open(self.backupfile, 'w') as new_backup:
                new_backup.write(raw_backup.format(''))

        # file for putty containing the command that will be executed
        with open(self.execfile, 'w') as new_exec:
            # this probably does not work
            new_exec.write(tmux_command)

    @staticmethod
    def backup():
        subprocess.call([os.path.join(bin_path, 'putty.exe'), '-pw',
                         settings['password'], '-ssh',
                         'robot@{}'.format(settings['ip']), '-m',
                         os.path.join(bin_path, 'backup.txt'), '-t'])
        print('\033[32mDone\033[00m')

    @staticmethod
    def copy_files():
        subprocess.call([os.path.join(bin_path, 'pscp.exe'), '-pw',
                         settings['password'], '-r', src_path,
                         'robot@{ip}:/home/robot/'.format(ip=settings['ip'],
                                                          home=home)])
        print('\033[32mDone\033[00m')

    @staticmethod
    def execute():
        subprocess.call([os.path.join(bin_path, 'putty.exe'), '-pw',
                         settings['password'], '-ssh',
                         'robot@{}'.format(settings['ip']), '-m',
                         os.path.join(bin_path, 'exec.txt'), '-t'])
        pass


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
        print('\033[32mDone\033[00m')

    @staticmethod
    def copy_files():
        subprocess.call(['sshpass', '-p', settings['password'], 'scp', '-o',
                         'StrictHostKeyChecking=no', '-r',
                         os.path.join(src_path),
                         'robot@{}:/home/robot/'.format(
            settings['ip'])])
        print('\033[32mDone\033[00m')

    @staticmethod
    def execute():
        # command = "; ".join((backup_command, tmux_command))
        command = tmux_command
        subprocess.call(['sshpass', '-p', settings['password'],
            'ssh','robot@{}'.format(settings['ip']), '-t', command])
        print('\033[32mJob finished\033[00m')


def main(copy=True, backup=True):
    global settings
    if not os.path.exists(settings_path):
        first_start()

    with open(settings_path) as file:
        settings = json.load(file)
    print('OS:', settings['os'])
    # switch to platform specific routines
    system = Windows(settings) if settings['os'] == 'Windows' else Unix(settings)
    if backup:
        print('\033[33mINFO\033[00m - Backup old files')
        system.backup()
    if copy:
        print('\033[33mINFO\033[00m - Copy new files:')
        system.copy_files()
    print('\033[33mINFO\033[00m - Executing')
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
    print('\r\033[31mJob canceled by user!\033[00m')
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

usage = '''Usage:
./ev3deploy [-n] [-e]

-n      Create new Config(IP, Password, Main-Script)
-e      Only execute code on Roboter, no data will be copied'''

if __name__ == '__main__':
    argv = sys.argv
    if len(argv) == 1:
        print('\033[33mINFO: If you have to change IP,\n\
      password or the executed file run\n      .\ev3deploy -n\033[00m')
        main()
    elif len(argv) == 2 or len(argv) == 3:
        match = False
        if '-n' in argv:
            match = True
            first_start()
        if '-e' in argv:
            match = True
            main(copy=False)
        if not match:
            print(usage)
    else:
        print(usage)
        sys.exit(0)
