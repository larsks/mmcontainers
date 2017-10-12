from __future__ import print_function
from __future__ import absolute_import

import fnmatch

from mmcontainers.app.caching import CachingApp


class CacheDumpApp(CachingApp):

    def create_argparser(self):
        p = super(CacheDumpApp, self).create_argparser()

        p.add_argument('pattern', nargs='*')

        return p

    def main(self):
        if not self.args.pattern:
            self.args.pattern = '*'

        for k in self.cache:
            if any(fnmatch.fnmatch(k, pattern)
                   for pattern in self.args.pattern):
                print(k)
                print(self.cache[k])
                print('---')

app = CacheDumpApp()
