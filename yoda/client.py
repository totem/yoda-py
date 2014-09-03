__author__ = 'sukrit'

import etcd
import time
from .model import Host, Location


def as_upstream(app_name, app_version, private_port):
    return '%s-%s-%s' % (app_name, app_version, private_port)


def as_endpoint(backend_host, backend_port):
    return '%s-%s' % (backend_host, backend_port)


class Client:
    """
    Yoda Client class
    """
    def __init__(self, etcd_cl=None, etcd_port=4001,
                 etcd_host='localhost', etcd_base='/yoda' ):
        """
        Initializes etcd client.
        :param etcd_cl:
        :param etcd_port:
        :param etcd_host:
        :return:
        """
        if not etcd_cl:
            self.etcd_cl = etcd.Client(host=etcd_host, port=etcd_port)
        else:
            self.etcd_cl = etcd_cl
        self.etcd_base = etcd_base

    def get_nodes(self, upstream, wait=False, wait_timeout=10):
        """
        Get nodes for a given upstream
        :param upstream: Upstream whose nodes needs to be determined.
        :type upstream: str
        :return: Dictionary of nodes for the upstream
        :rtype: dict
        """
        endpoints_key = '{etcd_base}/upstreams/{upstream}/endpoints'.format(
            etcd_base=self.etcd_base, upstream=upstream
        )
        try:
            endpoints = self.etcd_cl.read(endpoints_key, recursive=True)
        except KeyError:
            return dict()
        return dict((endpoint.key, endpoint.value)
                    for endpoint in endpoints.children)

    def wait_for_nodes(self, upstream, min_nodes=1, timeout=300,
                       retry_wait=10):
        """
        Waits for minimal no. of nodes to be available for a given upstream
        :param upstream:
        :param min_nodes:
        :param timeout: timeout in seconds
        :param retry_wait:
        :return: Dictionary of nodes for the upstream
        :rtype: dict
        :raises:
            TimeoutError: If timed out waiting for the nodes.
        """
        timer = 0
        while timer < timeout:
            nodes = self.get_nodes(upstream)
            if len(nodes) >= min_nodes:
                return nodes
            time.sleep(retry_wait)
            timer += retry_wait
        raise TimeoutError("Timed out waiting for at-least %d node(s) for "
                           "upstream %s" % (min_nodes, upstream))


    def discover_node(self, upstream, node_name, endpoint, ttl=300):
        node_key = '{etcd_base}/upstreams/{upstream}/endpoints/{node}' \
            .format(
            etcd_base=self.etcd_base, upstream=upstream, node=node_name)
        self.etcd_cl.set(node_key, endpoint, ttl=ttl)


    def wire_proxy(self, host):
        for location in host.locations:
            location_base = \
                '{etcd_base}/hosts/{hostname}/locations/{location_name}' \
                    .format(etcd_base=self.etcd_base, hostname=host.hostname,
                            location_name=location.location_name)
            self.etcd_cl.set('%s/path'%(location_base), location.path)
            for acl in location.allowed_acls:
                self.etcd_cl.set('%s/acls/allowed/%s'%(location_base, acl),
                                 acl)
            for acl in location.denied_acls:
                self.etcd_cl.set('%s/acls/denied/%s'%(location_base, acl),
                                 acl)
            self.etcd_cl.set('%s/upstream' % location_base, location.upstream)

    def unwire_proxy(self, hostname, upstreams=[]):
        host_base = '{etcd_base}/hosts/{hostname}'.format(
            etcd_base=self.etcd_base, hostname=hostname)
        self.etcd_cl.delete(host_base, recursive=True)
        for upstream in upstreams:
            upstream_base = '{etcd_base}/upstreams/{upstream}'.format(
                etcd_base=self.etcd_base, upstream=upstream)
            self.etcd_cl.delete(upstream_base, recursive=True)



if __name__ == "__main__":
    client = Client(etcd_host='etcd.melt.sh', etcd_base='/yoda-not-production')
    upstream=as_upstream('totem-spec-python', '1409692366903', 8080)
    print(client.get_nodes(upstream))
    client.wait_for_nodes(upstream, timeout=15)
    client.wire_proxy(
        Host('spec-python.cu.melt.sh', locations=[
            Location(upstream)
        ]))