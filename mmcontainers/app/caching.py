import diskcache

from mmcontainers.app.base import BaseApp
from mmcontainers import defaults


class CachingApp(BaseApp):
    shards = 8

    def create_argparser(self):
        p = super(CachingApp, self).create_argparser()

        g = p.add_argument_group('Cache options')
        g.add_argument('--cache-path', '-c',
                       default=defaults.cache_path)

        return p

    def prepare(self):
        cache = diskcache.FanoutCache(self.args.cache_path,
                                      shards=self.shards,
                                      eviction_policy='none')
        self.cache = diskcache.Index.fromcache(cache)
