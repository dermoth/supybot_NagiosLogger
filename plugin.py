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
import supybot.world as world
import supybot.ircmsgs as ircmsgs

import libpyzmq
import threading
import struct

class NagiosLogger(callbacks.Plugin):
    """This plugin receives alert notifications from Nagios and show them in
    channel. The only configuration needed is running the client on a Nagios
    server. See the client script for more details."""
    threaded = False

    def __init__(self, irc):
        self.__parent = super(NagiosLogger, self)
        self.__parent.__init__(irc)

        self.tp = threading.Thread(target=self.Listener)
        self.tp.setDaemon(True)
        self.tp.start()

    def _get_irc(self, network):
        for irc in world.ircs:
            if irc.network == network:
                return irc

    def _get_person_or_channel(self, irc, personorchannel):
        if personorchannel.startswith('#'):
            for channel in irc.state.channels:
                if channel == personorchannel:
                    return channel
        else:
            return personorchannel

    def _get_irc_and_target(self, network, personorchannel):
        target_irc = self._get_irc(network)
        if target_irc is None:
            raise Exception('Not on Network: %s' % network)
        target = self._get_person_or_channel(target_irc, personorchannel)
        if target is None:
            raise Exception('Not on Channel: %s' % personorchannel)
        return target_irc, target

    def Listener(self):
        ctx = libpyzmq.Context(1, 1)
        socket = libpyzmq.Socket(ctx, libpyzmq.SUB)
        socket.setsockopt(libpyzmq.SUBSCRIBE, '')
        #socket.bind(self.registryValue('ZmqURL')) #Doesn't work, help!
        socket.bind('tcp://0.0.0.0:12543')

        while True:

            msg = socket.recv()
            print "msg:", msg

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

            self.LogEvent("server", "notype", 1, "hostname", "service", "message")
            self.LogEvent(server, notype, stateid, hostname, service, message)


    def LogEvent(self, server, notype, stateid, hostname, service, message):
        # Get the IRC object and target FIXME: Try block - will throw an exception if not yet in channel
        irc, tgt = self._get_irc_and_target('NETWORK', '#CHANNEL')

        # TODO: Colorization
        if service is not '':
            statemap = {0: 'OK', 1: 'WARNING', 2: 'CRITICAL', 3: 'UNKNOWN'}
            msg = "%s %s: %s %s %s: %s" % (server, notype, hostname, service, statemap[stateid], message)
        else:
            statemap = {0: 'UP', 1: 'DOWN', 2: 'UNREACHABLE'}
            msg = "%s %s: %s %s: %s" % (server, notype, hostname, statemap[stateid], message)

        # TODO: Add channel parameter
        # FIXME: Try block - will throw exception if message contains invalid characters
        # TODO: Split lines and send multiple messages if necessary
        # FIXME: Use queueMsg()
        print tgt, msg
        tgt_msg = ircmsgs.privmsg(tgt, msg)
        irc.sendMsg(tgt_msg)
        #irc.(msg, prefixNick=False, to='#CHANNEL')


Class = NagiosLogger


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
