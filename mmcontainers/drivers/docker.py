from __future__ import print_function
from __future__ import absolute_import

import backoff
import docker
import json
import logging
import requests
import threading
import urllib3

LOG = logging.getLogger(__name__)

RETRY_EXCEPTIONS = (
    urllib3.exceptions.HTTPError,
    requests.exceptions.RequestException,
    docker.errors.DockerException
)


class DockerWatcher(threading.Thread):
    '''Monitor the Docker event stream.

    After connecting to the Docker events API, we also request a list
    of currently running containers.
    '''

    def __init__(self, cache, prefix='docker', apiversion=None):
        super(DockerWatcher, self).__init__()
        self.setDaemon(True)

        if apiversion is None:
            apiversion = 'auto'

        self.prefix = prefix
        self.cache = cache
        self.apiversion = apiversion

        self.create_logger()

    def create_logger(self):
        self.log = logging.getLogger('{}.{}'.format(
            self.__module__, self.__class__.__name__))

    @backoff.on_exception(backoff.expo, RETRY_EXCEPTIONS)
    def create_api(self):
        self.log.info('connecting to docker api')
        self.api = docker.from_env(version=self.apiversion)

    def run(self):
        self.create_api()

        self.threads = []
        self.threads.append(threading.Thread(target=self.watch))
        for t in self.threads:
            t.setDaemon(True)
            t.start()

        # populate the cache with information about currently running
        # containers
        for container in self.api.containers.list():
            self.add_container(container.id)

        for t in self.threads:
            t.join()

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

    @backoff.on_exception(backoff.expo, RETRY_EXCEPTIONS)
    def watch(self):
        self.log.info('starting to watch docker events')
        events = (json.loads(e.decode('utf8')) for e in self.api.events())
        for event in events:
            self.log.debug('received %s event for %s %s',
                           event.get('Action'), event.get('Type'),
                           event.get('Actor', {}).get('ID'))

            if event.get('Type') != 'container':
                continue
            if event.get('Action') not in ['start', 'die']:
                continue

            if event['Action'] == 'start':
                self.add_container(event['id'])
            elif event['status'] == 'die':
                self.remove_container(event['id'])
