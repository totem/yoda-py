__author__ = 'sukrit'

__all__ = ['as_endpoint', 'as_upstream', 'Location', 'Host', 'Client']

from .client import Client, as_endpoint, as_upstream
from .model import Host, Location
