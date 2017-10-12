from __future__ import print_function
from __future__ import absolute_import

import logging
import threading
import time
import urllib3

from kubernetes import client, config, watch  # NOQA


class KubeWatcher(object):
    def __init__(self, cache, prefix='kube', config_file=None):
        self.prefix = prefix
        self.cache = cache
        self.config_file = config_file

        self.create_logger()
        self.create_api()

    def create_logger(self):
        self.log = logging.getLogger('{}.{}'.format(
            self.__module__, self.__class__.__name__))

    def create_api(self):
        config.load_kube_config(config_file=self.config_file)
        self.api = client.CoreV1Api()

    def start(self):
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

    def join(self):
        for t in self.threads:
            t.join()

    def watch(self, endpoint, cache_key_fmt):
        w = watch.Watch()
        while True:
            try:
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
                        del self.cache[cache_key]
                    elif event['type'] in ['MODIFIED', 'ADDED']:
                        self.log.info('add %s', cache_key)
                        self.cache[cache_key] = data
            except urllib3.exceptions.HTTPError:
                time.sleep(1)
