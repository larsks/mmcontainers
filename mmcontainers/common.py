from __future__ import absolute_import
from __future__ import print_function

import logging
import time

LOG = logging.getLogger(__name__)


def backoff(initial=1, maxinterval=30, reset=None):
    '''An exponential backoff...thingy.

    Used in retry loops in which we want to retry a failed connection
    with exponential backoff behavior.
    '''

    if reset is None:
        reset = maxinterval

    interval = initial
    t0 = time.time()
    while True:
        t1 = time.time()
        if (t1 - t0) > reset:
            interval = initial

        time.sleep(interval)
        t0 = time.time()
        yield interval

        interval = min(interval * 2, maxinterval)
