"""
This code is junk!!!11!!!1!

# OLD COMMANDS
# these are just here for reference
#
# check for tmux session
#'if ! (tmux -S /tmp/tmux/shared has-session -t "ev3-robolab-startup" 2> /dev/null);
#
# try to clear tmux history
#'"import os" ENTER "os.system(\'tmux -S /tmp/tmux/shared send-keys -t ev3-robolab-startup -R\; send-keys -t ev3-robolab-startup C-l\;\')" ENTER'
"""

def build_call(password):
    # the command that reloads the python modules in tmux and attaches to the
    # session afterwards

    systemd_command_if = 'if ! (systemctl status ev3-robolab-startup \
    | grep "python" 1> /dev/null); \
    then echo "{}" | sudo -S systemctl restart ev3-robolab-startup > /dev/null'.format(password)

    command = "; ".join((systemd_command_if,
                         tmuxify_send(tmuxify('systemd_error.py')
                                      + ' ' + tmuxify('cls.py')
                                      + ' ' + tmuxify('systemd_error_print.py')
                                      + ' ' + tmuxify('run.py')),
                         'sleep 15s',
                         'else ' + tmuxify_send(tmuxify('blacklist.py')
                                                + ' '
                                                + tmuxify('reload.py')),
                         'fi',
                         tmuxify_attach()))
    print(command)
    return command
def tmuxify(file):
    with open('./tmuxify/' + file) as f:
        return '"' + '" ENTER "'.join(line.strip('\n') for line in f) + '" ENTER ENTER' # double ENTER needed as python is running in interactive mode

def tmuxify_send(payload):
    """
    """
    return 'tmux -S /tmp/tmux/shared send -t ev3-robolab-startup {}'.format(payload)

def tmuxify_attach():
    """
    Command to attach to a tmux session
    """
    return 'tmux -S /tmp/tmux/shared attach -t ev3-robolab-startup'
