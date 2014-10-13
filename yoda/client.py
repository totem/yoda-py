__author__ = 'sukrit'

import etcd
import os
from yoda.model import Host, Location


def as_upstream(app_name, app_version, private_port):
    return '%s-%s-%s' % (app_name, app_version, private_port)


def as_endpoint(backend_host, backend_port):
    return '%s:%s' % (backend_host, backend_port)


class Client:
    """
    Yoda Client that uses etcd API to control the proxy,
    """
    def __init__(self, etcd_cl=None, etcd_port=None,
                 etcd_host=None, etcd_base=None):
        """
        Initializes etcd client.
        :param etcd_cl:
        :param etcd_port:
        :param etcd_host:
        :return:
        """
        if not etcd_cl:
            self.etcd_cl = etcd.Client(
                host=etcd_host or 'localhost',
                port=etcd_port or 4001)
        else:
            self.etcd_cl = etcd_cl
        self.etcd_base = etcd_base or '/yoda'

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

    def discover_node(self, upstream, node_name, endpoint, ttl=120,
                      mode='http'):
        node_key = '{etcd_base}/upstreams/{upstream}/endpoints/{node}' \
            .format(etcd_base=self.etcd_base, upstream=upstream,
                    node=node_name)
        self.etcd_cl.set(node_key, endpoint, ttl=ttl)

    def discover_proxy_node(self, node_name, host='172.17.42.1', ttl=300):
        node_key = '{etcd_base}/proxy-nodes/{node}' \
            .format(etcd_base=self.etcd_base, node=node_name)
        self.etcd_cl.set(node_key, host, ttl=ttl)

    def __etcd_safe_delete(self, key, **kwargs):
        try:
            self.etcd_cl.delete(key, **kwargs)
        except KeyError:
            # Ignore
            pass

    def remove_node(self, upstream, node_name):
        node_key = '{etcd_base}/upstreams/{upstream}/endpoints/{node}' \
            .format(etcd_base=self.etcd_base, upstream=upstream,
                    node=node_name)
        self.__etcd_safe_delete(node_key)

    def remove_proxy_node(self, node_name):
        node_key = '{etcd_base}/proxy-nodes/{node}' \
            .format(etcd_base=self.etcd_base, node=node_name)
        self.__etcd_safe_delete(node_key)

    def update_tcp_listener(self, tcp_listener):
        """
        Creates or updates tcp listener for yoda proxy.
        :param tcp_listener:
        :type tcp_listener: yoda.model.TcpListener
        :return: None
        """
        listener_key = '/global/listeners/tcp/%s' % tcp_listener.name
        self.etcd_cl.set('%s/bind' % listener_key, tcp_listener.bind)
        if tcp_listener.upstream:
            self.etcd_cl.set('%s/upstream' % listener_key, upstream)

        def next_acl(acls):
            for acl in acls:
                yield acl

        for acl in next_acl(tcp_listener.allowed_acls):
            self.etcd_cl.set('%s/acls/allowed/%s' % (listener_key, acl),
                             acl)

        for acl in next_acl(tcp_listener.denied_acls):
            self.etcd_cl.set('%s/acls/denied/%s' % (listener_key, acl),
                             acl)

    def remove_tcp_listener(self, listener_name):
        """
        Deletes listener with listener_name if it exists. Has no effect if
        listener does not exists.
        :param listener_name: Unique Name for the listener
        :type listener_name: str
        :return: None
        """
        listener_key = '{etcd_base}/global/listeners/tcp/{listener}' \
            .format(etcd_base=self.etcd_base, node=listener_name)
        self.__etcd_safe_delete(listener_key)

    def wire_proxy(self, host):
        mapped_locations = []
        locations_key = '{etcd_base}/hosts/{hostname}/locations'.format(
            etcd_base=self.etcd_base, hostname=host.hostname
        )
        for location in host.locations:
            location_key = '%s/%s' % (locations_key, location.location_name)
            self.etcd_cl.set('%s/path' % (location_key), location.path)
            for acl in location.allowed_acls:
                self.etcd_cl.set('%s/acls/allowed/%s' % (location_key, acl),
                                 acl)
            for acl in location.denied_acls:
                self.etcd_cl.set('%s/acls/denied/%s' % (location_key, acl),
                                 acl)
            self.etcd_cl.set('%s/upstream' % location_key, location.upstream)
            mapped_locations.append(location.location_name)

        # Now cleanup unmapped paths
        for location in self.etcd_cl.read(
                locations_key, consistent=True).children:
            location_name = os.path.basename(location.key)
            if location_name not in mapped_locations:
                self.__etcd_safe_delete(location.key, recursive=True)

    def unwire_proxy(self, hostname, upstreams=[]):
        host_base = '{etcd_base}/hosts/{hostname}'.format(
            etcd_base=self.etcd_base, hostname=hostname)
        self.__etcd_safe_delete(host_base, recursive=True)
        for upstream in upstreams:
            upstream_base = '{etcd_base}/upstreams/{upstream}'.format(
                etcd_base=self.etcd_base, upstream=upstream)
            self.__etcd_safe_delete(upstream_base, recursive=True)


if __name__ == "__main__":
    client = Client(etcd_host='localhost', etcd_base='/yoda-local')
    upstream = as_upstream('totem-spec-python', '1409692366903', 8080)
    print(client.get_nodes(upstream))
    # client.wait_for_nodes(upstream, timeout=60)
    client.wire_proxy(
        Host('spec-python.cu.melt.sh', locations=[
            Location(upstream)
        ]))
    client.unwire_proxy('spec-python.cu.melt.sh', upstreams=[upstream])
    client.unwire_proxy('spec-python.cu.melt.sh', upstreams=[upstream])
