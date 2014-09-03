__author__ = 'sukrit'



__all__ = ['as_endpoint', 'as_upstream', 'Location', 'Host', 'Client']

from .client import Client
from .model import Host, Location


def as_upstream(app_name, app_version, private_port):
    return '%s-%s-%s' % (app_name, app_version, private_port)


def as_endpoint(backend_host, backend_port):
    return '%s-%s'