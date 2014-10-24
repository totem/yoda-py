"""
Test for yoda.client
"""
from nose.tools import eq_

from yoda.client import as_upstream

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
