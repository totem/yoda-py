__author__ = 'sukrit'

import re

INVALID_LOCATION_CHARS = re.compile('[^A-Za-z\\-0-9]+')


class Location:
    def __init__(self, upstream, path='/', location_name=None,
                 allowed_acls=['public'], denied_acls=['global-black-list'],
                 min_nodes=1):
        self.upstream = upstream
        self.path = path
        self.location_name = INVALID_LOCATION_CHARS.sub(
            '-', location_name or path)
        self.allowed_acls = allowed_acls
        self.denied_acls = denied_acls

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.upstream == other.upstream and \
            self.path == other.path and \
            self.location_name == other.location_name and \
            self.allowed_acls == other.allowed_acls and \
            self.denied_acls == other.denied_acls


class Host:
    def __init__(self, hostname, locations):
        self.locations = locations
        self.hostname = hostname

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return self.locations == other.locations and \
            self.hostname == other.hostname
