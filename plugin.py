###
# Copyright (c) 2010, Thomas Guyot-Sionnest
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import libpyzmq
import struct

class NagiosLogger(callbacks.Plugin):
    """This plugin receives alert notifications from Nagios and show them in
    channel. The only configuration needed is running the client on a Nagios
    server. See the client script for more details."""
    threaded = False

    def __init__(self, irc):
        self.__parent = super(NagiosLogger, self)
        self.__parent.__init__(irc)

        self.ctx = libpyzmq.Context(1, 1)
        self.socket = libpyzmq.Socket(self.ctx, libpyzmq.SUB)
        self.socket.setsockopt(libpyzmq.SUBSCRIBE, '')
        #self.socket.bind(self.registryValue('ZmqURL')) #Doesn't work, help!
        self.socket.bind('tcp://0.0.0.0:12543')

        # FIXME: threaded Listener goes here


    def Listener(irc)
        while True:
            msg = self.socket.recv()

            # Format is: server(str)[Tab]notificationtype(str)[Tab]stateid(int)[Tab]host(str)[Tab]service(str)[Tab]message(str)
            try:
                msgarray = msg.split('\t', 5)
                server = msgarray[0]
                notype = msgarray[1]
                stateid = int(msgarray[2])
                hostname = msgarray[3]
                service = msgarray[4]
                message = msgarray[5]
            except ValueError:
                # FIXME: log bad message
                pass
            except IndexError:
                # FIXME: log bad message
                pass

            self.LogEvent(server, irc, notype, stateid, hostname, service, message)


    def LogEvent(self, irc, server, notype, stateid, hostname, service, message):
        # TODO: Colorization
        if service is not '':
            statemap = {0: 'OK', 1: 'WARNING', 2: 'CRITICAL', 3: 'UNKNOWN'}
            msg = "%s %s: %s %s %s: %s" % (server, notype, hostname, service, statemap[stateid], message)
        else:
            statemap = {0: 'UP', 1: 'DOWN', 2: 'UNREACHABLE'}
            msg = "%s %s: %s %s: %s" % (server, notype, hostname, statemap[stateid], message)

        # TODO: Add channel parameter
        irc.reply(msg, prefixNick=False, to='#CHANNEL')


Class = NagiosLogger


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
