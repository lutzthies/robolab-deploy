import sys, os, traceback
try:
    reloader.reload(main)
except:
    absolutely_unused_variable = os.system('clear')
    print('Reload failed.')
    traceback.print_exc(file=sys.stdout)
else:
    absolutely_unused_variable = os.system('clear')
    print('Reload successful.')
    try:
        main.run()
    except:
        traceback.print_exc(file=sys.stdout)
    if main.client:
        main.client.loop_stop()
    for motor in ev3.list_motors():
        motor.stop()
