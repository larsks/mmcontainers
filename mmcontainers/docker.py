from __future__ import print_function
from __future__ import absolute_import

import docker
import json
import logging
import threading
import urllib3

from mmcontainers.common import restart_on

LOG = logging.getLogger(__name__)


class DockerWatcher(object):
    def __init__(self, cache, prefix='docker', apiversion=None):
        if apiversion is None:
            apiversion = 'auto'

        self.prefix = prefix
        self.cache = cache
        self.apiversion = apiversion

        self.create_api()
        self.create_logger()

    def create_logger(self):
        self.log = logging.getLogger('{}.{}'.format(
            self.__module__, self.__class__.__name__))

    def create_api(self):
        self.api = docker.from_env(version=self.apiversion)

    def start(self):
        self.threads = []

        self.threads.append(threading.Thread(target=self.watch))

        for t in self.threads:
            t.setDaemon(True)
            t.start()

        # populate the cache with information about currently running
        # containers
        for container in self.api.containers.list():
            self.add_container(container.id)

    def cache_key(self, cid):
        return '{prefix}/{id}'.format(
            prefix=self.prefix, id=cid)

    def add_container(self, cid):
        cache_key = self.cache_key(cid)
        self.log.info('add %s', cache_key)
        try:
            container = self.api.containers.get(cid)
        except docker.errors.NotFound:
            self.log.error('container %s does not exist', cid)
            return

        data = {
            'kind': 'container',
            'metadata': {
                'labels': container.labels,
                'image': container.image.id,
            }
        }

        self.cache[cache_key] = data

    def remove_container(self, cid):
        cache_key = self.cache_key(cid)
        self.log.info('remove %s', cache_key)

        del self.cache[cache_key]

    def join(self):
        for t in self.threads:
            t.join()

    @restart_on((urllib3.exceptions.HTTPError,))
    def watch(self):
        events = (json.loads(e) for e in self.api.events())
        for event in events:
            if event.get('Type') != 'container':
                continue
            if event.get('Action') not in ['create', 'destroy']:
                continue

            if event['Action'] == 'create':
                self.add_container(event['id'])
            elif event['status'] == 'destroy':
                self.remove_container(event['id'])
