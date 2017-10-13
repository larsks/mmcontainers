from __future__ import print_function
from __future__ import absolute_import

import logging
import threading
import urllib3

import kubernetes

from mmcontainers.common import retry_on

RETRY_EXCEPTIONS = (
    urllib3.exceptions.HTTPError,
)


class KubeWatcher(threading.Thread):
    def __init__(self, cache, prefix='kube', config_file=None):
        super(KubeWatcher, self).__init__()

        self.prefix = prefix
        self.cache = cache
        self.config_file = config_file

        self.setDaemon(True)
        self.create_logger()

    def create_logger(self):
        self.log = logging.getLogger('{}.{}'.format(
            self.__module__, self.__class__.__name__))

    def create_api(self):
        kubernetes.config.load_kube_config(config_file=self.config_file)
        self.api = kubernetes.client.CoreV1Api()

    def run(self):
        self.create_api()

        self.threads = []

        self.threads.append(threading.Thread(
            target=self.watch,
            args=(self.api.list_pod_for_all_namespaces,
                  '{prefix}/{metadata.namespace}/{metadata.name}')))
        self.threads.append(threading.Thread(
            target=self.watch,
            args=(self.api.list_namespace,
                  '{prefix}/{metadata.name}')))

        for t in self.threads:
            t.setDaemon(True)
            t.start()

        for t in self.threads:
            t.join()

    @retry_on(RETRY_EXCEPTIONS)
    def watch(self, endpoint, cache_key_fmt):
        self.log.info('starting to watch kubernetes events')
        w = kubernetes.watch.Watch()
        for event in w.stream(endpoint):
            cache_key = cache_key_fmt.format(
                metadata=event['object'].metadata,
                prefix=self.prefix)

            data = {
                'kind': event['object'].kind,
                'metadata': event['object'].metadata.to_dict(),
                'status': event['object'].status.to_dict(),
            }

            if event['type'] == 'DELETED':
                self.log.info('remove %s', cache_key)
                try:
                    del self.cache[cache_key]
                except KeyError:
                    pass
            elif event['type'] in ['MODIFIED', 'ADDED']:
                self.log.info('add %s', cache_key)
                self.cache[cache_key] = data
