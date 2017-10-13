from __future__ import absolute_import
from __future__ import print_function

import functools
import logging
import time

LOG = logging.getLogger(__name__)


def retry_on(exceptions, maxretries=None, reset=10, maxinterval=30):
    '''Retry a method with exponential backoff.'''

    def outer(func):

        @functools.wraps(func)
        def inner(*args, **kwargs):
            interval = 1
            tries = 0

            while True:
                try:
                    t0 = time.time()
                    func(*args, **kwargs)
                    break
                except exceptions as err:
                    t1 = time.time()

                    tries += 1
                    if maxretries and tries > maxretries:
                        raise

                    if (t1-t0) > reset:
                        interval = 1

                    LOG.error('{name} failed ({exception}), '
                              'retrying in {interval} seconds'.format(
                                  name=func.__name__,
                                  exception=err.__class__.__name__,
                                  interval=interval))

                    time.sleep(interval)
                    interval = min(interval * 2, maxinterval)

        return inner

    return outer
