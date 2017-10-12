from __future__ import print_function
from __future__ import absolute_import

import docker
import json
import logging
import threading
import urllib3
import requests

from mmcontainers.common import backoff

LOG = logging.getLogger(__name__)
RETRY_EXCEPTIONS = (
    urllib3.exceptions.HTTPError,
    requests.exceptions.RequestException,
    docker.errors.DockerException
)


class DockerWatcher(threading.Thread):
    def __init__(self, cache, prefix='docker', apiversion=None):
        super(DockerWatcher, self).__init__()

        if apiversion is None:
            apiversion = 'auto'

        self.prefix = prefix
        self.cache = cache
        self.apiversion = apiversion

        self.create_logger()

    def create_logger(self):
        self.log = logging.getLogger('{}.{}'.format(
            self.__module__, self.__class__.__name__))

    def create_api(self):
        interval = backoff(maxinterval=30)

        while True:
            try:
                self.api = docker.from_env(version=self.apiversion)
                break
            except RETRY_EXCEPTIONS as err:
                self.log.warning('caught exception %s (%s); retrying',
                                 type(err), err)
                next(interval)

    def run(self):
        self.create_api()
        self.threads = []

        self.threads.append(threading.Thread(target=self.restart_watch))

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

        try:
            del self.cache[cache_key]
        except KeyError:
            pass

    def join(self):
        for t in self.threads:
            t.join()

    def restart_watch(self):
        interval = backoff(maxinterval=30)

        while True:
            try:
                self.watch()
            except RETRY_EXCEPTIONS as err:
                self.log.warning('caught exception %s (%s); retrying',
                                 type(err), err)
                next(interval)

    def watch(self):
        events = (json.loads(e) for e in self.api.events())
        for event in events:
            self.log.debug('received %s event for %s',
                           event.get('Action'), event.get('Actor'))
            if event.get('Type') != 'container':
                continue
            if event.get('Action') not in ['start', 'die']:
                continue

            if event['Action'] == 'start':
                self.add_container(event['id'])
            elif event['status'] == 'die':
                self.remove_container(event['id'])
