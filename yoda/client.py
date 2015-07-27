import etcd
import os.path

__author__ = 'sukrit'


def as_upstream(app_name, private_port, app_version=None):
    """
    Creates upstream using application name, private port and version.

    :param app_name: Application Name
    :type app_name: str
    :param private_port: Private port for application (e.g. 8080)
    :type private_port: str or int
    :param app_version: Optional application version to be used for creating
     upstream. Defaults to None.
    :type app_version: str
    :return: String representing Upstream for yoda.
    :rtype: str
    """
    if app_version:
        # Used for Blue Green Deploys
        return '%s-%s-%s' % (app_name, app_version, private_port)
    else:
        # Used for A/B, Red Green deploy
        return '%s-%s' % (app_name, private_port)


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

    def get_nodes(self, upstream):
        """
        Get nodes for a given upstream
        :param upstream: Upstream whose nodes needs to be determined.
        :type upstream: str
        :return: Dictionary of nodes for the upstream. e.g.:
        {
            'node1': 'host1:port1',
            'node2': 'host2:port1',
        }
        :rtype: dict
        """
        endpoints_key = '{etcd_base}/upstreams/{upstream}/endpoints'.format(
            etcd_base=self.etcd_base, upstream=upstream
        )
        try:
            endpoints = self.etcd_cl.read(endpoints_key, recursive=True)
        except KeyError:
            return dict()
        return dict((os.path.basename(endpoint.key), endpoint.value)
                    for endpoint in endpoints.children)

    def register_upstream(self, upstream, mode='http', health_uri=None,
                          health_timeout=None, health_interval=None,
                          ttl=3600):
        """
        Registers upstream with give name, mode and health check params.

        :param upstream: Upstream (backend) that needs to be registered
        :type upstream: str
        :keyword mode: Proxy mode ('http' or 'tcp'). Defaults to 'http'
        :type mode: str
        :keyword health_uri: URI to be used for http health check. If None,
            http health check is not executed.
        :type health_uri: str
        :keyword health_timeout: Timeout for healthcheck. (e.g.: '5s').
            Defaults to None. If None, it uses haproxy's default timeout for
            health-check
        :type health_timeout: str
        :keyword health_interval: Frequency for health check. If None (default)
            it defaults to value specified in haproxy cfg template.
        :type health_interval: str
        :keyword ttl: Time to live for upstream directory.
        :type ttl: int
        :return: None
        """
        upstream_key = '%s/upstreams/%s' % (self.etcd_base, upstream)

        # Delete existing upstream if it exists.
        self.remove_upstream(upstream)
        self.etcd_cl.write(upstream_key, None, ttl=ttl, dir=True)
        self.etcd_cl.set('%s/mode' % upstream_key, mode)
        if health_uri:
            self.etcd_cl.set('%s/health/uri' % upstream_key, health_uri)
        if health_timeout:
            self.etcd_cl.set('%s/health/timeout' % upstream_key,
                             health_timeout)
        if health_interval:
            self.etcd_cl.set('%s/health/interval' % upstream_key,
                             health_interval)

    def remove_upstream(self, upstream):
        """
        Removes upstream with given name if it exists.

        :param upstream: Name of upstream (or backend)
        :type upstream: str
        :return:None
        """
        self._etcd_safe_delete('%s/upstreams/%s' % (self.etcd_base, upstream),
                               recursive=True, dir=True)

    def renew_upstream(self, upstream, ttl=3600):
        """
        Renews the TTL for an existing upstream to ensure that it does not get
        removed.

        :param upstream: Upstream for the node.
        :keyword ttl: Time to live for Etcd record
        :type ttl: int
        :return: None
        """
        upstream_key = '%s/upstreams/%s' % (self.etcd_base, upstream)
        self.etcd_cl.write(upstream_key, None, ttl=ttl, dir=True,
                           prevExist=True)

    def discover_node(self, upstream, node_name, endpoint, ttl=120):
        """
        Discover nodes for a given upstream

        :param upstream: Upstream for the node.
        :type upstream: str
        :param node_name: Name of the node to be discovered
        :type node_name: str
        :param endpoint: Discover endpoint (host:port)
        :type endpoint: str
        :param ttl: Time to live for Etcd record
        :type ttl: int
        :return:
        """
        upstream_key = '{etcd_base}/upstreams/{upstream}' \
            .format(etcd_base=self.etcd_base, upstream=upstream)
        node_key = '{upstream_key}/endpoints/{node}' \
            .format(upstream_key=upstream_key, node=node_name)
        self.etcd_cl.set(node_key, endpoint, ttl=ttl)

    def discover_proxy_node(self, node_name, host='172.17.42.1', ttl=300):
        node_key = '{etcd_base}/proxy-nodes/{node}' \
            .format(etcd_base=self.etcd_base, node=node_name)
        self.etcd_cl.set(node_key, host, ttl=ttl)

    def _etcd_safe_delete(self, key, **kwargs):
        try:
            self.etcd_cl.delete(key, **kwargs)
        except KeyError:
            # Ignore
            pass

    def remove_node(self, upstream, node_name):
        node_key = '{etcd_base}/upstreams/{upstream}/endpoints/{node}' \
            .format(etcd_base=self.etcd_base, upstream=upstream,
                    node=node_name)
        self._etcd_safe_delete(node_key)

    def remove_proxy_node(self, node_name):
        node_key = '{etcd_base}/proxy-nodes/{node}' \
            .format(etcd_base=self.etcd_base, node=node_name)
        self._etcd_safe_delete(node_key)

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
            self.etcd_cl.set('%s/upstream' % listener_key,
                             tcp_listener.upstream)

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
        self._etcd_safe_delete(listener_key)

    def _setup_aliases(self, hostname, aliases):
        aliases_key = '{etcd_base}/hosts/{hostname}/aliases'.format(
            etcd_base=self.etcd_base, hostname=hostname)
        for alias in aliases or []:
            self.etcd_cl.set('{0}/{1}'.format(aliases_key, alias), alias)

    def wire_proxy(self, host):
        """
        Wires the proxy for all locations of a given host.

        :param host:
        :type host: yoda.model.Host
        :return:
        """
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
            if location.force_ssl:
                self.etcd_cl.set('%s/force-ssl' % location_key, 'true')
            mapped_locations.append(location.location_name)

        # Now cleanup unmapped paths
        for location in self.etcd_cl.read(
                locations_key, consistent=True).children:
            location_name = os.path.basename(location.key)
            if location_name not in mapped_locations:
                self._etcd_safe_delete(location.key, recursive=True)
        self._setup_aliases(host.hostname, host.aliases)

    def unwire_proxy(self, hostname, upstreams=[]):
        host_base = '{etcd_base}/hosts/{hostname}'.format(
            etcd_base=self.etcd_base, hostname=hostname)
        self._etcd_safe_delete(host_base, recursive=True)
        for upstream in upstreams:
            upstream_base = '{etcd_base}/upstreams/{upstream}'.format(
                etcd_base=self.etcd_base, upstream=upstream)
            self._etcd_safe_delete(upstream_base, recursive=True)
