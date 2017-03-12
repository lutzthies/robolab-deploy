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
    """
    Builds the huge bash script that seeks for python and tmux running as our service, automatically restarts them in case they are not running and attaches to the session aftwards, then reloading the source files and running them from main.run()
    """

    systemd_command_if = 'if ! (systemctl status ev3-robolab-startup \
    | grep "python" 1> /dev/null); \
    then echo "Whoops, looks like somebody messed with our tmux session"; \
         echo "Restarting the service (THIS MAY TAKE SOME TIME)"; \
         echo "{}" | sudo -S -p "" systemctl restart ev3-robolab-startup > /dev/null'.format(password)

    command = "; ".join((systemd_command_if,
                         tmuxify_send('systemd_error.py',
                                      'cls.py',
                                      'systemd_error_print.py',
                                      'run.py'),
                         'sleep 15s',
                         'else ' + tmuxify_send('blacklist.py',
                                                'reload.py'),
                         'fi',
                         tmuxify_attach()))
    return command

def tmuxify(file):
    """
    Prepare any file to be send by tmuxify_send()
    """
    with open('./tmuxify/' + file) as f:
        return '"' + '" ENTER "'.join(line.strip('\n') for line in f) + '" ENTER'

def tmuxify_send(*payload):
    """
    Send something via tmux :)
    """
    chained = " ".join(tmuxify(i) for i in payload)
    return 'tmux -S /tmp/tmux/shared send -t ev3-robolab-startup {} ENTER'.format(chained) # causes double ENTER needed as python is running in interactive mode

def tmuxify_attach():
    """
    Attach to a tmux session
    """
    return 'tmux -S /tmp/tmux/shared attach -t ev3-robolab-startup'
