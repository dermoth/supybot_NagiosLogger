#!/usr/bin/env python
#
# NagiosLogger Client
# Author: Thomas Guyot-Sionnest <tguyot@gmail.com>
#

import sys, libpyzmq


def LogEvent(URL, server, notype, stateid, host, service, message):
    # Raw stateid test - will throw an exception if failed
    int(stateid)

    ctx = libpyzmq.Context(1, 1)
    socket = libpyzmq.Socket(ctx, libpyzmq.PUB)
    socket.connect(URL)

    # Format is: server(str)[Tab]notificationtype(str)[Tab]stateid(int)[Tab]host(str)[Tab]service(str)[Tab]message(str)
    msg = ''.join([server, "\t", notype, "\t", stateid, "\t", host, "\t", service, "\t", message])
    socket.send(msg)
    # FIXME: Use a reliable mechanism - this is the workaround
    import time
    time.sleep(1)

def usage(error=None):
    if error:
        print 'Error:', error
    print
    print 'Usage:', sys.argv[0], '<ZMQ_URL> <Server> <Notification Type> <Service State ID> <Host> <Service Desc> <Message>'
    print 'Usage:', sys.argv[0], '<ZMQ_URL> <Server> <Notification Type> <Host State ID> <Host> <Message>'
    if error: sys.exit(1)
    sys.exit(0)

if len(sys.argv) > 1 and sys.argv[1] in ('-h', '--help'):
    usage()
elif len(sys.argv) == 7:
    # Host notification
    LogEvent(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], '', sys.argv[6])
    print "Successfully sent Host Alert event to", sys.argv[1]
elif len(sys.argv) == 8:
    # Service notification
    LogEvent(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7])
    print "Successfully sent Service Alert event to", sys.argv[1]
else:
    usage('Wrong number of arguments')


