from __future__ import print_function
from __future__ import absolute_import

import datetime
import fnmatch
import json

from mmcontainers.app.caching import CachingApp


def serialize_datetime(v):
    if isinstance(v, datetime.datetime):
        return v.isoformat()


class CacheDumpApp(CachingApp):

    def create_argparser(self):
        p = super(CacheDumpApp, self).create_argparser()

        p.add_argument('--keys-only', '-K',
                       action='store_true',
                       help='only display cache keys')
        p.add_argument('--values-only', '-V',
                       action='store_true',
                       help='only display cache values')
        p.add_argument('pattern', nargs='*')

        return p

    def main(self):
        if not self.args.pattern:
            self.args.pattern = '*'

        for k in self.cache:
            if any(fnmatch.fnmatch(k, pattern)
                   for pattern in self.args.pattern):

                if not self.args.values_only:
                    print(k)

                if not self.args.keys_only:
                    print(json.dumps(self.cache[k],
                                     default=serialize_datetime))

app = CacheDumpApp()
