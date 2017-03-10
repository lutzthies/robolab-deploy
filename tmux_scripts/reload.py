import os
try:
    reloader.reload(main)
except Exception as e:
    absolutely_unused_variable = os.system('clear')
    print('Reload failed. This exception occured:', e)
else:
    absolutely_unused_variable = os.system('clear')
    print('Reload successful.')
    main.run()
