import json
import sys


class RsyslogFilter(object):
    '''Handle rsyslog messages in `fulljson` format'''

    def __init__(self, stream=None, handler=None):
        self.stream = stream if stream else sys.stdin
        if handler is not None:
            self.handle_message = handler

    def messages(self):
        '''Yield a stream of messages.

        Reads JSON-encoded messages from stdin, decodes them into
        Python data structures, and yields them to the caller.
        '''

        while True:
            msg = self.stream.readline()
            if not msg:
                break

            yield(json.loads(msg))

    def handle_message(self, msg):
        raise NotImplementedError('You have not configured a message handler')

    def run(self):
        '''Start the main filter loop.

        Pass each message received from rsyslog to the message handler
        for processing, and then convert the result to JSON before
        writing it back to stdout.
        '''

        for msg in self.messages():
            sys.stdout.write(json.dumps(self.handle_message(msg)))
            sys.stdout.write('\n')
            sys.stdout.flush()
