# mmcontainers: an rsyslog filter for gathering container metadata

This is a message modification plugin for [rsyslog][] that annotates
log messages from containers with metadata obtained from both
Docker and Kubernetes.

This filter relies on metadata provided by the [journald logging
driver][], so you will need to be running Docker with `--log-driver
journald`.

## Requirements

This requires a version of [rsyslog][] with support for external
filters (the `mmexternal` plugin).  There exists [a bug in
rsyslog][#1822] in all versions up to and including 8.29.0 that
results in a crash when using external filters; you will need a fix
for [#1822][] in order for this to operate correctly.

[#1822]: https://github.com/rsyslog/rsyslog/issues/1822

There is patched version of rsyslog for RHEL/CentOS 7 available from
<https://copr.fedorainfracloud.org/coprs/larsks/rsyslog/>.

## Usage

There are two parts to this solution.

`mmcontainers-monitor` listens for events from Docker and Kubernetes
and writes metadata to a persistent cache.

`mmcontainers-filter` is the rsyslog filter, which receives messages
from rsyslog, looks up associated information in the cache maintained
by `mmcontainers-monitor`, and adds the metadata to the log messages.

### mmcontainers-monitor

Listens to event streams from Docker and Kubernetes and maintains a
metadata cache for use by `mmcontainers-filters`.

Synopsis:

    usage: mmcontainers-monitor [-h] [--verbose] [--debug]
                                [--cache-path CACHE_PATH] [--watch-kubernetes]
                                [--kube-config-file KUBE_CONFIG_FILE]
                                [--watch-docker]

Options:

- `--cache-path` -- path to persistent cache
- `--watch-docker`, `-D` -- listen for events from Docker
- `--watch-kubernetes`, `-K` -- listen for events from Kubernetes

### mmcontainers-filter

This is the filter for use with the [rsyslog mmexternal module][].

[rsyslog mmexternal module]: http://www.rsyslog.com/doc/v8-stable/configuration/modules/mmexternal.html

Synopsis:

    usage: mmcontainers-filter [-h] [--verbose] [--debug]
                               [--cache-path CACHE_PATH]
                               [--include-docker-metadata]
                               [--include-kubernetes-metadata]

Options:

- `--cache-path` -- path to persistent cache
- `--include-docker-metadata`, `-D` -- annotate log messages with
  Docker labels
- `--include-kubernetes-metadata`, `-K` -- annotate log messages with
  Kubernetes labels and annotations

### mmcontainers-cachedump

A tool for inspecting the `mmcontainers` cache.

Synopsis:

    usage: mmcontainers-cachedump [-h] [--verbose] [--debug]
                                  [--cache-path CACHE_PATH] [--keys-only]
                                  [pattern [pattern ...]]

Options:

- `--cache-path` -- path to persistent cache
- `--keys-only`, `-k` -- display only keys, rather than dumping keys
  and values

By default `mmcontainers-cachedump` will dump all cache keys, but you
can limit it to specific keys by providing a glob-style pattern.  For
example, so show only metadata from docker:

    mmcontainers-cachedump 'docker/*'

## Example

Given an input message from journald that contains:

    {
      ...
      "CONTAINER_ID": "0379e173018b",
      "CONTAINER_ID_FULL": "0379e173018b846b8c997429603933392ef8d1953b5b203d0223207bfd4d3167",
      "CONTAINER_NAME": "k8s_thttpd_thttpd_testproject_005e222a-ab0d-11e7-a756-5254005d0480_1",
      ...
    }

This filter will add metadata from docker and kubernetes to the
message:

    {
      "docker": {
        "image": "sha256:a31ab5050b671bf43f64dba89d799e844fd7f9b907836d36e8fb711bb96fdd99",
        "labels": {
          "annotation.io.kubernetes.pod.terminationGracePeriod": "30",
          "annotation.io.kubernetes.container.terminationMessagePolicy": "File",
          "io.kubernetes.pod.namespace": "testproject",
          "io.kubernetes.pod.name": "thttpd",
          "io.kubernetes.container.logpath": "/var/log/pods/005e222a-ab0d-11e7-a756-5254005d0480/thttpd_2.log",
          "annotation.io.kubernetes.container.restartCount": "2",
          "io.kubernetes.container.name": "thttpd",
          "annotation.io.kubernetes.container.hash": "4fac039c",
          "annotation.io.kubernetes.container.ports": "[{\"containerPort\":7070,\"protocol\":\"TCP\"}]",
          "io.kubernetes.docker.type": "container",
          "io.kubernetes.pod.uid": "005e222a-ab0d-11e7-a756-5254005d0480",
          "annotation.io.kubernetes.container.terminationMessagePath": "/dev/termination-log",
          "io.kubernetes.sandbox.id": "c415e8adda626065e95cc7b1fb5e1d4de6596e5522572752f7af57c99c2bb539"
        }
      },
      "kubernetes": {
        "labels": {
          "cluster": "testcluster",
          "zone": "us-east-coast"
        },
        "namespace": "testproject",
        "name": "thttpd",
        "annotations": {
          "builder": "john-doe",
          "openshift.io/scc": "restricted",
          "build": "two"
        }
      }
      ...
    }

## Configuring rsyslog

See [rsyslog.conf](rsyslog.conf) for an example configuration.

[rsyslog]: http://www.rsyslog.com/
[kubernetes]: https://kubernetes.io/
[journald logging driver]: https://docs.docker.com/engine/admin/logging/journald/
