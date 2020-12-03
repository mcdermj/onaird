from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.defer import Deferred
import re


class CommandFailure(Exception):
    def __init__(self, errno: int, message: str) -> None:
        super().__init__()
        self.errno = errno
        self.message = message


class SsdrApiProtocol(LineOnlyReceiver):
    delimiter = b'\n'

    def __init__(self) -> None:
        self.minor_version = 0.0
        self.major_version = 0.0
        self.handle = 0x00
        self.sequence = 0
        self.meters = {}
        self.slices = {}
        self.completion_list = {}
        self.response_matcher = re.compile(r'R([0-9]+)\|([0-9A-Z]{0,8})\|?(.*)')

    @staticmethod
    def __parse_line(line: str):
        line_args = []
        line_kwargs = {}
        for token in line.split():
            if '=' in token:
                k, v = token.split('=')
                line_kwargs[k] = v
            else:
                line_args.append(token)
        return line_args, line_kwargs

    def send_command(self, command: str) -> Deferred:
        self.sendLine('C{}|{}'.format(self.sequence, command).encode('utf-8'))
        print('Sending: "C{}|{}"'.format(self.sequence, command))
        d = Deferred()
        self.completion_list[self.sequence] = d
        self.sequence += 1
        return d

    def response_received(self, line: str) -> None:
        match = self.response_matcher.match(line)
        print('Recieved response: "{}"'.format(line))
        if match == None:
            print("Couldn't parse response line: {}".format(line))
            return

        sequence = int(match.group(1))
        errno = int(match.group(2), 16)
        message = match.group(3)

        if sequence not in self.completion_list:
            print("Couldn't find sequence {} in completion list".format(sequence))
            return

        if errno == 0:
            self.completion_list[sequence].callback(message)
        else:
            self.completion_list[sequence].errback(CommandFailure(errno, message))

    def command_received(self, line):
        pass

    def status_received(self, line):
        line = line.split('|')[1]
        tokens = line.split()

        if tokens[0] == 'slice':
            sliceno = tokens[1]
            if sliceno not in self.slices:
                self.slices[sliceno] = {}
            for token in tokens[2:]:
                try:
                    (name, value) = token.split('=')
                except ValueError:
                    self.slices[sliceno][token] = ''
                else:
                    self.slices[sliceno][name] = value
            self.update_settings()

    def message_received(self, line):
        pass

    def lineReceived(self, line):
        line = line.decode('utf-8')

        if line[0] == 'V':
            return
        elif line[0] == 'H':
            return
        elif line[0] == 'R':
            self.response_received(line)

        command, line = line.split('|')
        line_args, line_kwargs = SsdrApiProtocol.__parse_line(line)

        if command[0] == 'C':
            pass
        elif command[0] == 'S':
            method_handler = getattr(self, '{}_status_handler'.format(line_args[0]), None)
            if method_handler is not None:
                method_handler(line_args, line_kwargs)
        elif command[0] == 'M':
            method_handler = getattr(self, '{}_message_handler'.format(line_args[0]), None)
            if method_handler is not None:
                method_handler(line_args, line_kwargs)
        else:
            print('Invalid command: {}', line)


class SsdrApiClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        return SsdrApiProtocol()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)
