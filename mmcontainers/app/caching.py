import diskcache

from mmcontainers.app.base import BaseApp
from mmcontainers import defaults


class CachingApp(BaseApp):
    def create_argparser(self):
        p = super(CachingApp, self).create_argparser()

        g = p.add_argument_group('Cache options')
        g.add_argument('--cache-path', '-c',
                       default=defaults.cache_path)

        return p

    def prepare(self):
        self.cache = diskcache.Index(self.args.cache_path)
