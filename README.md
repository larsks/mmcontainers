# mmkubernetes: an rsyslog filter for gathering Kubernetes metadata

This is a message modification plugin for [rsyslog][] that annotates
log messages from containers running under [Kubernetes][] with metadata
retrieved from the Kubernetes API.

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

## Example

Given an input message from journald that contains:

    {
      ...
      "CONTAINER_ID": "0379e173018b",
      "CONTAINER_ID_FULL": "0379e173018b846b8c997429603933392ef8d1953b5b203d0223207bfd4d3167",
      "CONTAINER_NAME": "k8s_thttpd_thttpd_testproject_005e222a-ab0d-11e7-a756-5254005d0480_1",
      ...
    }

This filter will add a `k8s` key to the message metadata that contains
information about the pod in which the container was running,
including the pod name, namespace, annotations, and labels:

    {
      ...
      "k8s": {
        "pod_labels": {
          "cluster": "testcluster",
          "zone": "us-east-coast"
        },
        "pod_namespace": "testproject",
        "pod_name": "thttpd",
        "pod_annotations": {
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
