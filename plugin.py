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

import libpyzmq
import threading
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class NagiosLogger(callbacks.Plugin):
    """This plugin receives alert notifications from Nagios and show them in
    channel. The only configuration needed is running the client on a Nagios
    server. See the client script for more details."""
    threaded = False

    # Some colormaps

    # Notification type map
    notype_cmap = {
            'PROBLEM': 'red',
            'RECOVERY': 'green',
            'ACKNOWLEDGEMENT': 'blue',
            'FLAPPINGSTART': 'red',
            'FLAPPINGSTOP': 'green',
            'FLAPPINGDISABLED': 'orange',
            'DOWNTIMESTART': 'dark grey',
            'DOWNTIMEEND': 'dark grey',
            'DOWNTIMECANCELLED': 'orange',
    }

    # Alert type map
    state_cmap = {
            'UP': 'green',
            'DOWN': 'red',
            'UNREACHABLE': 'orange',
            'OK': 'green',
            'WARNING': 'yellow',
            'UNKNOWN': 'orange',
            'CRITICAL': 'red',
    }

    def __init__(self, irc):
        self.__parent = super(NagiosLogger, self)
        self.__parent.__init__(irc)

        self.tp = threading.Thread(target=self.listener)
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

    def listener(self):
        ctx = libpyzmq.Context(1, 1)
        socket = libpyzmq.Socket(ctx, libpyzmq.REP)
        #socket.bind(self.registryValue('ZmqURL')) # TODO: Doesn't work, help!
        socket.bind('tcp://0.0.0.0:12543')

        while True:

            msg = socket.recv()
            socket.send('Ack!')

            # Format is:
            # server(str)[Tab]notifi_type(str)[Tab]stateid(int)[Tab]host(str)
            #   [Tab]service(str)[Tab]message(str)
            try:
                msgarray = msg.split('\t', 5)
                server = msgarray[0]
                notype = msgarray[1]
                stateid = int(msgarray[2])
                hostname = msgarray[3]
                service = msgarray[4]
                message = msgarray[5]
            except ValueError:
                self.log.error('NagiosLogger: Received message is invalid')
            except IndexError:
                self.log.error('NagiosLogger: Received message is invalid '
                               'or incomplete')

            self.logEvent(server, notype, stateid,
                          hostname, service, message)


    def logEvent(self, server, notype, stateid, hostname, service, message):
        # Get the IRC object and target
        # TODO: Queue up messages if not on channel yet?
        try:
            # TODO: add channel parameter
            (irc, tgt) = self._get_irc_and_target('NETWORK', '#CHANNEL')
        except Exception, e:
            # Likely cause is not being on channel yet
            self.log.error('NagiosLogger: Getting context failed: %s' % (str(e),))
            return

        # TODO: Wrap around color map, allowing unknown types
        try:
            if service is not '':
                statemap = {0: 'OK', 1: 'WARNING', 2: 'CRITICAL', 3: 'UNKNOWN'}
                msg = format('%s %s %s %s %s %s',
                    ircutils.mircColor(server, fg='dark grey'),
                    ircutils.mircColor(ircutils.bold(notype + ':'),
                        fg=NagiosLogger.notype_cmap[notype]),
                    ircutils.mircColor(hostname, fg='black'),
                    ircutils.mircColor(ircutils.underline(service),
                        fg='purple'),
                    ircutils.mircColor(ircutils.bold(statemap[stateid] + ':'),
                        fg=NagiosLogger.state_cmap[statemap[stateid]]),
                    ircutils.mircColor(ircutils.underline(message), fg='teal')
                    )
            else:
                statemap = {0: 'UP', 1: 'DOWN', 2: 'UNREACHABLE'}
                msg = format('%s %s %s %s %s',
                    ircutils.mircColor(server, fg='dark grey'),
                    ircutils.mircColor(ircutils.bold(notype + ':'),
                        fg=NagiosLogger.notype_cmap[notype]),
                    ircutils.mircColor(hostname, fg='black'),
                    ircutils.mircColor(ircutils.bold(statemap[stateid] + ':'),
                        fg=NagiosLogger.state_cmap[statemap[stateid]]),
                    ircutils.mircColor(ircutils.underline(message), fg='teal')
                    )
        except KeyError:
            self.log.error('NagiosLogger: Message contain invalid fields')
            return

        # TODO: Split lines and send multiple messages if necessary
        try:
            tgt_msg = ircmsgs.privmsg(tgt, msg)
            irc.queueMsg(tgt_msg)
        except AssertionError:
            self.log.error('NagiosLogger: Sending message failed, this may '
                           'be caused by invalid characters in it')


Class = NagiosLogger


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
