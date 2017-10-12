#!/usr/bin/env python

import argparse
import diskcache
import daiquiri
import os
import rsyslog
import signal

from mmcontainers.docker import DockerWatcher
from mmcontainers.kubernetes import KubeWatcher

LOG = daiquiri.getLogger(__name__)
DEFAULT_CACHE_PATH = os.path.expanduser('~/.cache/mmcontainers')


class Filter(rsyslog.filter.RsyslogFilter):
    default_metadata_keys = ['name', 'namespace']

    def __init__(self, cache,
                 namespace=None,
                 include_annotations=False,
                 include_labels=False,
                 metadata_keys=None,
                 **kwargs):
        self.cache = cache
        self.namespace = namespace

        if metadata_keys is not None:
            self.metadata_keys = set(metadata_keys)
        else:
            self.metadata_keys = set(self.default_metadata_keys)

        if include_labels:
            self.metadata_keys.add('labels')

        if include_annotations:
            self.metadata_keys.add('annotations')

        super(Filter, self).__init__(**kwargs)

    def handle_message(self, msg):
        if '$!' not in msg or 'CONTAINER_ID_FULL' not in msg.get('$!'):
            return {}

        cache_key = 'docker://{}'.format(msg['$!']['CONTAINER_ID_FULL'])
        data = self.cache.get(cache_key)
        if data is None:
            return {}

        metadata = {}
        for k in self.metadata_keys:
            metadata['pod_{}'.format(k)] = data['metadata'][k]

        return {'$!': {self.namespace: metadata}}


def parse_args():
    p = argparse.ArgumentParser()

    g = p.add_argument_group('Cache options')
    g.add_argument('--cache-path', '-c',
                   default=DEFAULT_CACHE_PATH)

    g = p.add_argument_group('Kubernetes options')
    g.add_argument('--watch-kubernetes', '-K',
                   action='store_true')
    g.add_argument('--kube-config-file',
                   help='path to a kubernetes client configuration')

    g = p.add_argument_group('Docker options')
    g.add_argument('--watch-docker', '-D',
                   action='store_true')

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

    return p.parse_args()


def main():
    args = parse_args()
    daiquiri.setup(level=args.loglevel)
    cache = diskcache.FanoutCache(directory=args.cache_path,
                                  eviction_policy='none',
                                  shards=4)
    cache.clear()
    watchers = []

    if args.watch_kubernetes:
        LOG.debug('creating kubernetes watcher')
        kube = KubeWatcher(cache, config_file=args.kube_config_file)
        watchers.append(kube)

    if args.watch_docker:
        LOG.debug('creating docker watcher')
        dock = DockerWatcher(cache)
        watchers.append(dock)

    for watcher in watchers:
        watcher.start()

    LOG.debug('all watchers are running')
    signal.pause()

if __name__ == '__main__':
    main()
