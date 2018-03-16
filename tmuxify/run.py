import sys, os, traceback

def run():
    try:
        main.run()
    except:
        traceback.print_exc(file=sys.stdout)
    if main.client:
        main.client.loop_stop()
    for motor in ev3.list_motors():
        motor.stop()

run()
