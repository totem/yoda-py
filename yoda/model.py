__author__ = 'sukrit'

import re

INVALID_LOCATION_CHARS = re.compile('[^A-Za-z\\-]+')

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
    pass


class Host:
    def __init__(self, hostname, locations):
        self.locations = locations
        self.hostname = hostname
