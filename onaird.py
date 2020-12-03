#!/usr/bin/env python3

from twisted.internet import reactor
from ssdrapiclient import SsdrApiProtocol
from twisted.internet.protocol import ReconnectingClientFactory
import argparse
import gpiod


class OnAirProtocol(SsdrApiProtocol):
    def __init__(self):
        super().__init__()
        self.chip = gpiod.Chip('gpiochip0', gpiod.Chip.OPEN_BY_NAME)
        self.line = self.chip.get_line(26)
        self.line.request(consumer='onaird', type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

    def __del__(self):
        self.chip.close()

    def interlock_status_handler(self, args, kwargs):
        if 'state' not in kwargs:
            return

        if kwargs['state'] in 'READY':
            print("In RX")
            self.line.set_value(0)
        elif kwargs['state'] in 'TRANSMITTING':
            print("In TX")
            self.line.set_value(1)


class OnAirClientFactory(ReconnectingClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        self.resetDelay()
        return OnAirProtocol()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Drive the On Air sign from the radio information')
    parser.add_argument('radio_ip', help="IP address of the radio")

    args = parser.parse_args()

    reactor.connectTCP(args.radio_ip, 4992, OnAirClientFactory())
    reactor.run()
