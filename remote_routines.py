def build_call(password):
    #the command that reloads the python modules in tmux and attaches to the
    # session afterwards
    tmux_command = 'tmux -S /tmp/tmux/shared send -t ev3-robolab-startup \
    "reloader.enable(blacklist=[\'ev3dev\',\'ev3dev.ev3\',\'ev3\',\'typing\'])" ENTER \
    "reloader.reload(main)" ENTER \
    "main.run()" ENTER; \
    tmux -S /tmp/tmux/shared attach -t ev3-robolab-startup'

    tmux_cls = '"import os" ENTER "os.system(\'clear\')" ENTER'
    #tmux_cls = '"import os" ENTER "os.system(\'tmux -S /tmp/tmux/shared send-keys -t ev3-robolab-startup -R\; send-keys -t ev3-robolab-startup C-l\;\')" ENTER'

    # hey, I just met you and this is crazy...
    systemd_error = "\"beautiful_statement_and_noone_will_use_this_var = \'\
    \\033[31m################################################################################\\n\
    \\033[31m#\\033[0m\\033[93m                                                                              \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m          NOTICE - THE TMUX SESSION OR PYTHON WAS NOT RUNNING. SAD!           \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m                                                                              \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m It looks like you\\'ve somehow messed with our systemd service. DUH!           \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m                                                                              \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m Please stop doing so. Simply detach from the tmux session by pressing        \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m >>>>>>>>>>>>>>>>>>>>>> CTRL + B followed by hitting D <<<<<<<<<<<<<<<<<<<<<< \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m                                                                              \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m Thank you, we appreciate your cooperation. :)                                \\033[31m#\\n\
    \\033[31m#\\033[0m\\033[93m                                                                              \\033[31m#\\n\
    \\033[31m################################################################################\\033[0m\'\" ENTER"

    systemd_error_print =  '"print(beautiful_statement_and_noone_will_use_this_var)" ENTER'

    # command = "; ".join((backup_command, tmux_command))
    #systemd_command ='if ! (tmux -S /tmp/tmux/shared has-session -t \
    #"ev3-robolab-startup" 2> /dev/null); \
    systemd_command_if = 'if ! (systemctl status ev3-robolab-startup \
    | grep "python" 1> /dev/null); \
    then echo "{}" | sudo -S systemctl restart ev3-robolab-startup'.format(password)

    tmux_send = 'tmux -S /tmp/tmux/shared send -t ev3-robolab-startup'
    tmux_blacklist = '"reloader.enable(blacklist=[\'ev3dev\',\'ev3dev.ev3\',\'ev3\',\'typing\'])" ENTER'
    tmux_reload = '"reloader.reload(main)" ENTER'
    tmux_run = '"main.run()" ENTER'

    tmux_attach = 'tmux -S /tmp/tmux/shared attach -t ev3-robolab-startup'

    command = "; ".join((systemd_command_if, tmux_send + ' ' +
                         systemd_error + ' ' + tmux_cls, tmux_send + ' ' + systemd_error_print + ' ' + tmux_run,
                         'else ' + tmux_send + ' ' + tmux_blacklist + ' '+ tmux_reload + ' ' + tmux_cls + ' ' + tmux_run, 'fi',
                         tmux_attach))
    return command