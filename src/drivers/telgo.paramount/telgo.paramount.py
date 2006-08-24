#! /usr/bin/python

import sys
import string

from socket import *
import select

__description__ = "Paramount ME telgo wrapper"
__version__ = "0.1"
__date__  = "01/03/2004"

# parse arguments
if len(sys.argv) < 4:
    print """
    %s - versao %s - %s
    
    Usage: %s server[:port] ra dec
    Ex.  : %s localhost:10000 +12:12:12 21:21:21
           %s server +12:12:12 21:21:21
           %s - +12:12:12 21:21:21

    """ % (__description__, __version__, __date__,
           sys.argv[0], sys.argv[0], sys.argv[0], sys.argv[0])

    sys.exit(-1)


# get target host and port from command line
if ":" in sys.argv[1]:
    target = string.split(sys.argv[1], ":")
    target[1] = int(target[1])
elif sys.argv[1] != "-":
    target = [sys.argv[1], 10000]
else:
    target = [gethostname(), 10000]


# helpful names
targetRA = sys.argv[2]
targetDEC = sys.argv[3]

# connect, send coordinates, and wait until telescope stop

try:

    skt = socket(AF_INET, SOCK_STREAM)

    print "Connecting to %s:%d... wait... " % tuple(target)
    sys.stdout.flush()
    skt.connect(tuple(target))
    print "OK"
    
    skt.sendall("%s*%s*MOVE" % (targetRA, targetDEC))

    print "Moving to %s %s... wait... " % (targetRA, targetDEC)
    sys.stdout.flush()

    # wait until telescope move
    wait = select.select([skt], [], [skt], 60)

    if len(wait[0]) or len(wait[2]):
        data = skt.recv(256)

        if data == "OK":
            print "OK"
        else:
            print "ERROR (%s)" % data
    else:
            print "ERROR (Timeout)"

    skt.sendall("BYE")

    skt.close()
    sys.exit(0)

except KeyboardInterrupt:
    print "Ctrl+C... exiting..."
    skt.sendall("BYE")
    skt.close()
    sys.exit(1)

except error, e:
    print "ERROR (%s)" % (e[1])
    #skt.sendall("BYE")
    skt.close()
    sys.exit(1)
     
        



        




