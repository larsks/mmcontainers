from __future__ import print_function
from __future__ import absolute_import

import signal

from mmcontainers.app.caching import CachingApp
from mmcontainers.exc import ApplicationError

try:
    import mmcontainers.docker as mdocker
except ImportError:
    mdocker = None

try:
    import mmcontainers.kubernetes as mkubernetes
except ImportError:
    mkubernetes = None


class MonitorApp(CachingApp):

    def create_argparser(self):
        p = super(MonitorApp, self).create_argparser()

        if mkubernetes is not None:
            g = p.add_argument_group('Kubernetes options')
            g.add_argument('--watch-kubernetes', '-K',
                           action='store_true')
            g.add_argument('--kube-config-file',
                           help='path to a kubernetes client configuration')
        else:
            p.set_defaults(watch_kubernetes=False)

        if mdocker is not None:
            g = p.add_argument_group('Docker options')
            g.add_argument('--watch-docker', '-D',
                           action='store_true')
        else:
            p.set_defaults(watch_docker=False)

        return p

    def main(self):
        self.cache.clear()
        watchers = []

        if self.args.watch_kubernetes:
            self.log.debug('creating kubernetes watcher')
            kube = mkubernetes.KubeWatcher(
                self.cache, config_file=self.args.kube_config_file)
            watchers.append(kube)

        if self.args.watch_docker:
            self.log.debug('creating docker watcher')
            dock = mdocker.DockerWatcher(self.cache)
            watchers.append(dock)

        if len(watchers) == 0:
            raise ApplicationError('nothing to watch')

        for watcher in watchers:
            watcher.start()

        self.log.debug('all watchers are running')
        signal.pause()

app = MonitorApp()
