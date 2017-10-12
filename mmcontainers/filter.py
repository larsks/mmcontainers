from __future__ import print_function
from __future__ import absolute_import

import rsyslog

from mmcontainers.app.caching import CachingApp


class FilterApp(CachingApp):
    def create_argparser(self):
        p = super(FilterApp, self).create_argparser()

        p.add_argument('--include-docker-metadata', '-D',
                       action='store_true',
                       default=None)
        p.add_argument('--include-kubernetes-metadata', '-K',
                       action='store_true',
                       default=None)

        return p

    def prepare(self):
        super(FilterApp, self).prepare()
        self.filter = rsyslog.filter.RsyslogFilter(handler=self.handle_message)

    def main(self):
        # if neither -K or -D is specified, include both
        # docker and kubernetes metadata.
        if (self.args.include_docker_metadata is None and
                self.args.include_kubernetes_metadata is None):
            self.args.include_docker_metadata = True
            self.args.include_kubernetes_metadata = True

        self.filter.run()

    def add_docker_metadata(self, update, data):
        update['docker'] = {
            'labels': data['metadata']['labels'],
            'image': data['metadata']['image'],
        }

    def add_kubernetes_metadata(self, update, data):
        update['kubernetes'] = {
            'name': data['metadata']['name'],
            'namespace': data['metadata']['namespace'],
            'labels': data['metadata']['labels'],
            'annotations': data['metadata']['annotations'],
        }

    def handle_message(self, msg):
        cid = msg.get('$!', {}).get('CONTAINER_ID_FULL')
        if not cid:
            return {}

        update = {}

        cache_key = 'docker/{}'.format(cid)
        data = self.cache.get(cache_key)
        if data is None:
            return {}

        if self.args.include_docker_metadata:
            self.add_docker_metadata(update, data)

        if self.args.include_kubernetes_metadata:
            if 'io.kubernetes.pod.namespace' in data['metadata']['labels']:
                ns = data['metadata']['labels']['io.kubernetes.pod.namespace']
                pod = data['metadata']['labels']['io.kubernetes.pod.name']
                cache_key = 'kube/{}/{}'.format(ns, pod)
                data = self.cache.get(cache_key)
                if data is not None:
                    self.add_kubernetes_metadata(update, data)

        return {'$!': update}


app = FilterApp()
