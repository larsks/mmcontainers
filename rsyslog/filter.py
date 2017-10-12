import json
import sys


class RsyslogFilter(object):
    def __init__(self, stream=None, handler=None):
        self.stream = stream if stream else sys.stdin
        if handler is not None:
            self.handle_message = handler

    def messages(self):
        while True:
            msg = self.stream.readline()
            if not msg:
                break

            yield(json.loads(msg))

    def handle_message(self, msg):
        raise NotImplementedError('You have not configured a message handler')

    def run(self):
        for msg in self.messages():
            sys.stdout.write(json.dumps(self.handle_message(msg)))
            sys.stdout.write('\n')
            sys.stdout.flush()
