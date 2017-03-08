import re


def ip_check():
    """
    Asks to enter an IP address and checks its validity
    """
    valid_format = re.compile(r'(\d{1,3}\.){3}\d{1,3}$')
    final = ''
    while True:
        raw = input('Please enter the IP address: ')
        if valid_format.match(raw) is not None:
            sequences = raw.split('.')
            if int(sequences[0]) < 256 and int(sequences[1]) < 256\
               and int(sequences[2]) < 256 and int(sequences[3]) < 256:
                final = raw
                break
            else:
                print('Range of numbers in an IP address is from 0 to 255')
        else:
            print('IP has to match the format XXX.XXX.XXX.XXX')
    return final
