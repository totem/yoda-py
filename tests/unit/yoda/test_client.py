"""
Test for yoda.client
"""
import collections
import etcd
from mock import MagicMock
from nose.tools import eq_
from tests.helper import dict_compare
from yoda import Host, Location

from yoda.client import as_upstream, Client, as_endpoint

MOCK_APP_NAME = 'mock-app'
MOCK_APP_VERSION = 'mock-version'
MOCK_PRIVATE_PORT = 80
DEFAULT_TTL = 120


def test_as_upstream_with_version():
    """Should create upstream when version is supplied"""

    # When: I create upstream using version
    upstream = as_upstream(MOCK_APP_NAME, MOCK_PRIVATE_PORT, MOCK_APP_VERSION)

    # Then: Expected upstream is created
    eq_(upstream, 'mock-app-mock-version-80')


def test_as_upstream_without_version():
    """Should create upstream when version is supplied"""

    # When: I create upstream without using version
    upstream = as_upstream(MOCK_APP_NAME, MOCK_PRIVATE_PORT)

    # Then: Expected upstream is created
    eq_(upstream, 'mock-app-80')


def test_as_endpoint():
    """
    Should return endpoint the endpoint value for a given host, port
    """

    # When: I invoke as_endpoint with existing host and port
    endpoint = as_endpoint('mockhost', 40123)

    # Then: Expected upstream is created
    eq_(endpoint, 'mockhost:40123')


def test_client_init():
    """
    Should initialize etcd_client when etcd client instance is not passed
    explicitly
    """

    # When: I create new instance of yoda client
    client = Client()

    # Then: Client gets initialized as expected
    eq_(client.etcd_base, '/yoda')
    eq_(client.etcd_cl.host, 'localhost')
    eq_(client.etcd_cl.port, 4001)


class TestClient():
    KeyValue = collections.namedtuple('KeyValue', 'key,value')
    KeyChildren = collections.namedtuple('KeyChildren', 'key,children')

    def setup(self):
        self.etcd_cl = MagicMock(spec=etcd.Client)
        self.client = Client(etcd_cl=self.etcd_cl)

    def test_remove_upstream(self):
        """
        Should remove existing upstream.
        """

        # When: I remove existing upstream
        self.client.remove_upstream('test')

        # Then: The upstream with given name gets removed
        self.etcd_cl.delete.assert_called_with('/yoda/upstreams/test',
                                               recursive=True, dir=True)

    def test_register_upstream(self):
        """
        Should register upstream with given name.
        """

        # When: I register upstream with given name
        self.client.register_upstream('test')

        # Then: The upstream gets created successfully.
        self.etcd_cl.set.assert_called_once_with(
            '/yoda/upstreams/test/mode', 'http')
        self.etcd_cl.write.assert_called_with(
            '/yoda/upstreams/test', None, dir=True, ttl=3600)
        self.etcd_cl.delete.assert_called_once_with(
            '/yoda/upstreams/test', recursive=True, dir=True)

    def test_register_upstream_with_uri_timeout_interval(self):
        """
        Should register upstream with given name, health uri and timeout.
        """

        # When: I register upstream with given name, uri and timeout
        self.client.register_upstream('test', health_uri='/',
                                      health_timeout='5s',
                                      health_interval='5m')

        # Then: The upstream gets created successfully.
        self.etcd_cl.set.assert_any_call('/yoda/upstreams/test/mode', 'http')
        self.etcd_cl.set.assert_any_call('/yoda/upstreams/test/health/uri',
                                         '/')
        self.etcd_cl.set.assert_any_call('/yoda/upstreams/test/health/timeout',
                                         '5s')
        self.etcd_cl.set.assert_any_call(
            '/yoda/upstreams/test/health/interval', '5m')
        self.etcd_cl.write.assert_called_with(
            '/yoda/upstreams/test', None, dir=True, ttl=3600)
        self.etcd_cl.delete.assert_called_once_with(
            '/yoda/upstreams/test', recursive=True, dir=True)

    def test_discover_node(self):
        """
        Should register given node with etcd.
        """

        # When: I register node of a given upstream.
        self.client.discover_node('test', 'testnode', 'localhost:3434')

        # Then: My node gets registered successfully.
        self.etcd_cl.set.assert_any_call(
            '/yoda/upstreams/test/endpoints/testnode', 'localhost:3434',
            ttl=120)

    def test_discover_node_with_meta_info(self):
        """
        Should register given node with etcd.
        """

        # When: I register node of a given upstream.
        self.client.discover_node('test', 'testnode', 'localhost:3434', meta={
            'unit-no': 1,
            'service-name': 'mock@1.service'
        })

        # Then: My node gets registered successfully.
        self.etcd_cl.set.assert_any_call(
            '/yoda/upstreams/test/endpoints/testnode', 'localhost:3434',
            ttl=DEFAULT_TTL)
        self.etcd_cl.set.assert_any_call(
            '/yoda/upstreams/test/endpoints-meta/testnode/unit-no', 1,
            ttl=DEFAULT_TTL)
        self.etcd_cl.set.assert_any_call(
            '/yoda/upstreams/test/endpoints-meta/testnode/service-name',
            'mock@1.service', ttl=DEFAULT_TTL)

    def test_discover_proxy_node(self):
        """
        Should register proxy node
        """
        # When: I register proxy node
        self.client.discover_proxy_node('test', 'localhost')

        # Then: My proxy node gets registered successfully.
        self.etcd_cl.set.assert_called_once_with(
            '/yoda/proxy-nodes/test', 'localhost', ttl=300)

    def test_renew_upstream(self):
        """
        Should renew a given upstream
        """

        # When: I renew existing upstream
        self.client.renew_upstream('mock')

        # Then: My upstream gets registered as expected
        self.etcd_cl.write.assert_called_with(
            '/yoda/upstreams/mock', None, dir=True, ttl=3600, prevExist=True)

    def test_etcd_safe_delete_for_non_existing_key(self):
        # Given: Non existing key
        self.etcd_cl.delete.side_effect = KeyError('mock')

        # When: I perform a safe delete for mock key
        self.client._etcd_safe_delete('mock')

        # Then: No exception is thrown

    def test_wire_proxy(self):
        """
        Should wire proxy for existing host.
        """

        # Given: Existing host
        host = Host('mockhost', locations=[
            Location('upstream1', path='/path1'),
            Location('upstream2', path='/path2', force_ssl=True),
        ])

        # And: Existing Locations
        KeyValue = collections.namedtuple('KeyValue', 'key,value')
        self.etcd_cl.read.return_value.children = [
            KeyValue('/yoda/hosts/mockhost/locations/-path1', MagicMock()),
            KeyValue('/yoda/hosts/mockhost/locations/-path3', MagicMock())
        ]

        # When: I wire proxy for a given host
        self.client.wire_proxy(host)

        # Then: Proxy gets wired as expected
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path1/path', '/path1')
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path1/acls/allowed/public',
            'public')
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path1/acls/denied/'
            'global-black-list', 'global-black-list')
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path1/upstream', 'upstream1')
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path1/force-ssl', 'false')

        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path2/path', '/path2')
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path2/acls/allowed/public',
            'public')
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path2/acls/denied/'
            'global-black-list', 'global-black-list')
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path2/upstream', 'upstream2')
        self.etcd_cl.set.assert_any_call(
            '/yoda/hosts/mockhost/locations/-path2/force-ssl', 'true')

        self.etcd_cl.delete.assert_called_once_with(
            '/yoda/hosts/mockhost/locations/-path3', recursive=True)

    def test_setup_aliases(self):
        # Given: Aliases to be registered for a given hostname
        hostname = 'mockhost'
        aliases = ['mockalias1']

        # When: Setup aliases for the given host
        self.client._setup_aliases(hostname, aliases)

        # Then: Aliases gets registered as expected
        self.etcd_cl.set.assert_called_once_with(
            '/yoda/hosts/mockhost/aliases/mockalias1', 'mockalias1')

    def test_get_nodes(self):
        # Given: Existing nodes registered in etcd for given upstream

        self.etcd_cl.read.return_value.children = [
            self.KeyValue('/yoda/upstreams/test/endpoints/testnode1',
                          'host1:40001'),
            self.KeyValue('/yoda/upstreams/test/endpoints/testnode2',
                          'host2:40001'),
        ]

        # When: I get existing nodes
        nodes = self.client.get_nodes('test')

        # Then: Expected nodes is returned
        dict_compare(nodes, {
            'testnode1': 'host1:40001',
            'testnode2': 'host2:40001'
        })
        self.etcd_cl.read.assert_called_once_with(
            '/yoda/upstreams/test/endpoints', recursive=True)

    def test_get_nodes_with_meta(self):
        # Given: Existing nodes registered in etcd for given upstream

        endpoints = MagicMock()
        endpoints_meta = MagicMock()

        self.etcd_cl.read.side_effect = [endpoints, endpoints_meta]

        endpoints.children = [
            self.KeyValue('/yoda/upstreams/test/endpoints/testnode1',
                          'host1:40001'),
            self.KeyValue('/yoda/upstreams/test/endpoints/testnode2',
                          'host2:40001'),
        ]

        # And: Meta information for existing nodes
        endpoints_meta.children = [
            self.KeyChildren(
                '/yoda/upstreams/test/endpoints-meta/testnode1',
                [
                    self.KeyValue('/yoda/upstreams/test/endpoints-meta/'
                                  'testnode1/mockkey', 'mockval1'),
                ]),
            self.KeyChildren(
                '/yoda/upstreams/test/endpoints-meta/testnode2',
                [
                    self.KeyValue('/yoda/upstreams/test/endpoints-meta/'
                                  'testnode1/mockkey', 'mockval2'),
                ])
        ]

        # When: I get existing nodes
        nodes = self.client.get_nodes_with_meta('test')

        # Then: Expected nodes is returned
        dict_compare(nodes, {
            'testnode1': {
                'endpoint': 'host1:40001',
                'mockkey': 'mockval1'
            },
            'testnode2': {
                'endpoint': 'host2:40001',
                'mockkey': 'mockval2'
            }
        })
        self.etcd_cl.read.assert_has_call(
            '/yoda/upstreams/test/endpoints', recursive=True)
        self.etcd_cl.read.assert_has_call(
            '/yoda/upstreams/test/endpoints-meta', recursive=True)

    def test_get_nodes_for_non_existing_upstream(self):
        # Given: Existing nodes registered in etcd for given upstream

        self.etcd_cl.read.side_effect = KeyError

        # When: I get existing nodes
        nodes = self.client.get_nodes('test')

        # Then: Empty nodes dictionary is returned
        dict_compare(nodes, {})

    def test_get_nodes__with_meta_for_non_existing_upstream(self):
        # Given: Existing nodes registered in etcd for given upstream

        self.etcd_cl.read.side_effect = KeyError

        # When: I get existing nodes
        nodes = self.client.get_nodes_with_meta('test')

        # Then: Empty nodes dictionary is returned
        dict_compare(nodes, {})
