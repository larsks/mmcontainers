from __future__ import print_function
from __future__ import absolute_import

from mmcontainers.app.caching import CachingApp


class CacheDumpApp(CachingApp):

    def main(self):
        for k in self.cache:
            print(k)
            print(self.cache[k])
            print('---')

app = CacheDumpApp()
