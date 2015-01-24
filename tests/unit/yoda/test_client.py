"""
Test for yoda.client
"""
import etcd
from mock import MagicMock
from nose.tools import eq_

from yoda.client import as_upstream, Client

MOCK_APP_NAME = 'mock-app'
MOCK_APP_VERSION = 'mock-version'
MOCK_PRIVATE_PORT = 80


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


class TestClient():

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
                                               recursive=True)

    def test_register_upstream(self):
        """
        Should register upstream with given name.
        """

        # When: I register upstream with given name
        self.client.register_upstream('test')

        # Then: The upstream gets created successfully.
        self.etcd_cl.set.call_count = 1
        self.etcd_cl.set.assert_called_with('/yoda/upstreams/test/mode',
                                            'http')

    def test_register_upstream_with_uri_and_timeout(self):
        """
        Should register upstream with given name, health uri and timeout.
        """

        # When: I register upstream with given name, uri and timeout
        self.client.register_upstream('test', health_uri='/',
                                      health_timeout='5s')

        # Then: The upstream gets created successfully.
        self.etcd_cl.set.call_count = 3
        self.etcd_cl.set.assert_any_call('/yoda/upstreams/test/mode', 'http')
        self.etcd_cl.set.assert_any_call('/yoda/upstreams/test/health/uri',
                                         '/')
        self.etcd_cl.set.assert_any_call('/yoda/upstreams/test/health/timeout',
                                         '5s')

    def test_discover_node(self):
        """
        Should register given node with etcd.
        """

        # When: I register node of a given upstream.
        self.client.discover_node('test', 'testnode', 'localhost:3434')

        # Then: My node gets registered successfully.
        self.etcd_cl.set.call_count = 1
        self.etcd_cl.set.assert_called_with(
            '/yoda/upstreams/test/endpoints/testnode', 'localhost:3434',
            ttl=120)

    def test_discover_proxy_node(self):
        """
        Should register proxy node
        """
        # When: I register proxy node
        self.client.discover_proxy_node('test', 'localhost')

        # Then: My proxy node gets registered successfully.
        self.etcd_cl.set.call_count = 1
        self.etcd_cl.set.assert_called_with('/yoda/proxy-nodes/test',
                                            'localhost', ttl=300)
