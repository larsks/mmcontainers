#!/usr/bin/env python

import argparse
import datetime
import json
import sys
import threading
import time
import urllib3

from kubernetes import client, config, watch  # NOQA


def serialize_as_str(v):
    if isinstance(v, datetime.datetime):
        return str(v)
    elif hasattr(v, 'to_dict'):
        return v.to_dict()
    else:
        raise ValueError(type(v))


class KubeWatcher(object):
    def __init__(self, api, cache_dump_path=None):
        self.api = api
        self.cache_dump_path = cache_dump_path
        self.cache = {}
        self.lock = threading.RLock()

    def start(self):
        self.threads = []
        self.threads.append(threading.Thread(target=self.watch_namespaces))
        self.threads.append(threading.Thread(target=self.watch_pods))

        for t in self.threads:
            t.setDaemon(True)
            t.start()

    def join(self):
        for t in self.threads:
            t.join()

    def add(self, k, event):
        with self.lock:
            v = {
                'kind': event['object'].kind,
                'metadata': event['object'].metadata.to_dict(),
                'status': event['object'].status.to_dict(),
            }
            self.cache[k] = v

            if 'container_statuses' in v['status']:
                for container in v['status']['container_statuses']:
                    self.cache[container['container_id']] = v

            self.dump_cache()

    def remove(self, k):
        with self.lock:
            v = self.cache[k]
            del self.cache[k]
            if 'container_statuses' in v['status']:
                for container in v['status']['container_statuses']:
                    del self.cache[container['container_id']]
            self.dump_cache()

        return v

    def dump_cache(self):
        if self.cache_dump_path:
            with open(self.cache_dump_path, 'w') as fd:
                json.dump(self.cache, fd, indent=2, default=serialize_as_str)

    def watch_namespaces(self):
        w = watch.Watch()
        while True:
            try:
                for event in w.stream(self.api.list_pod_for_all_namespaces):
                    cache_key = '{}_{}'.format(
                        event['object'].metadata.namespace,
                        event['object'].metadata.name,
                    )

                    if event['type'] == 'DELETED':
                        self.remove(cache_key)
                    elif event['type'] in ['MODIFIED', 'ADDED']:
                        self.add(cache_key, event)
            except urllib3.exceptions.HTTPError:
                time.sleep(1)

    def watch_pods(self):
        w = watch.Watch()
        while True:
            try:
                for event in w.stream(self.api.list_namespace):
                    cache_key = event['object'].metadata.name

                    if event['type'] == 'DELETED':
                        self.remove(cache_key)
                    elif event['type'] in ['MODIFIED', 'ADDED']:
                        self.add(cache_key, event)
            except urllib3.exceptions.HTTPError:
                time.sleep(1)


class RsyslogFilter(object):
    def __init__(self, cache):
        self.cache = cache

    def messages(self):
        while True:
            msg = sys.stdin.readline()
            if not msg:
                break

            yield(json.loads(msg))

    def handle_message(self, msg):
        if '$!' not in msg or 'CONTAINER_ID_FULL' not in msg.get('$!'):
            return {}

        cache_key = 'docker://{}'.format(msg['$!']['CONTAINER_ID_FULL'])
        data = self.cache.get(cache_key)
        if data is None:
            return {}

        metadata = {}
        for k in ['name', 'namespace', 'labels', 'annotations', 'uid']:
            metadata['pod_{}'.format(k)] = data['metadata'][k]

        return {'$!': {'k8s': metadata}}

    def run(self):
        for msg in self.messages():
            sys.stdout.write(json.dumps(self.handle_message(msg)))
            sys.stdout.write('\n')
            sys.stdout.flush()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--config-file', '-f')
    p.add_argument('--cache-dump-path', '-d')

    return p.parse_args()


def main():
    args = parse_args()
    config.load_kube_config(config_file=args.config_file)
    api = client.CoreV1Api()

    watcher = KubeWatcher(api,
                          cache_dump_path=args.cache_dump_path)
    watcher.start()

    filter = RsyslogFilter(watcher.cache)
    filter.run()


if __name__ == '__main__':
    main()
