import argparse
import logging
import sys

from mmcontainers.exc import ApplicationError


class BaseApp(object):

    def create_argparser(self):
        p = argparse.ArgumentParser()

        g = p.add_argument_group('Logging options')
        g.add_argument('--verbose', '-v',
                       action='store_const',
                       const='INFO',
                       dest='loglevel')
        g.add_argument('--debug', '-d',
                       action='store_const',
                       const='DEBUG',
                       dest='loglevel')

        p.set_defaults(loglevel='WARNING')

        return p

    def parse_args(self):
        p = self.create_argparser()
        self.args = p.parse_args()

    def configure_logging(self):
        logging.basicConfig(level=self.args.loglevel)

    def create_logger(self):
        self.log = logging.getLogger('{}.{}'.format(
            self.__module__, self.__class__.__name__))

    def prepare(self):
        pass

    def cleanup(self):
        pass

    def main():
        raise NotImplementedError('application must define a main method')

    def run(self):
        try:
            self.parse_args()
            self.configure_logging()
            self.create_logger()
            self.prepare()
            self.main()
        except KeyboardInterrupt:
            pass
        except ApplicationError as err:
            self.log.error(str(err))
            sys.exit(1)
        finally:
            self.cleanup()
