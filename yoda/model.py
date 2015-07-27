import re

__author__ = 'sukrit'

INVALID_LOCATION_CHARS = re.compile('[^A-Za-z\\-0-9]+')


class Location:
    """
    Model representing location for yoda proxy.
    """
    def __init__(self, upstream, path='/', location_name=None,
                 allowed_acls=None, denied_acls=None, force_ssl=False):
        """
        Constructor

        :param upstream: Name of the upstream (backend) for this location.
        :type upstream
        :keyword path: Backend path to be used for proxy. (Default: '/')
        :type path: str
        :keyword location_name: A unique name for this location. If None, path
            is used as location with '/' replaced by '-'. (Default: None)
        :type location_name: str
        :keyword allowed_acls: List of allowed acl names. If None, defaults to
            ['public']. (Default: None)
        :type allowed_acls: list
        :keyword denied_acls: List of denied acl names. If None, defaults to
            ['global-black-list']. (Default: None)
        :type allowed_acls: list
        :keyword force_ssl: Boolean value specifying whether to force ssl for
            http requests. (Default: False)
        :type force_ssl: bool
        """
        self.upstream = upstream
        self.path = path
        self.location_name = INVALID_LOCATION_CHARS.sub(
            '-', location_name or path)
        self.allowed_acls = allowed_acls or ['public']
        self.denied_acls = denied_acls or ['global-black-list']
        self.force_ssl = force_ssl

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return 'Location(%s)' % str(self)

    def __eq__(self, other):
        return self.upstream == other.upstream and \
            self.path == other.path and \
            self.location_name == other.location_name and \
            self.allowed_acls == other.allowed_acls and \
            self.denied_acls == other.denied_acls and \
            self.force_ssl == other.force_ssl


class Host:
    """
    Model representing Host for yoda proxy.
    """
    def __init__(self, hostname, locations, aliases=None):
        """
        :param hostname: Hostname for proxy (e.g.: myapp.example.com)
        :type hostname: str
        :param locations: List of Location
        :type locations: list
        :keyword aliases: List of alias for the host
        :type aliases: list
        """
        self.locations = locations
        self.hostname = hostname
        self.aliases = aliases

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return 'Host(%s)' % str(self)

    def __eq__(self, other):
        return self.locations == other.locations and \
            self.hostname == other.hostname and \
            self.aliases == other.aliases


class TcpListener:
    """
    Model representing Tcp based listener for yoda proxy.
    """
    def __init__(self, name, bind, upstream=None, allowed_acls=None,
                 denied_acls=None):
        """
        Constructor for initializing TcpListener.
        :param name: Name for the listener( Alpha-numeric characters only)
        :type name: str
        :param bind: Bind address for TCP Listener. (e.g.: *:32768 will bind
            to all addressed on port 32768)
        :type bind: str
        :param upstream: Upstream for the listener. If none, no proxying will
            be done by proxy. (Default: None)
        :type upstream: str
        :param allowed_acls: List of allowed ACL strings. (Default: None)
        :type allowed_acls: list
        :param denied_acls: List of denied ACL strings. (Default: None)
        :type denied_acls: list
        :return: None
        """
        self.name = name
        self.bind = bind
        self.upstream = upstream
        self.allowed_acls = allowed_acls or []
        self.denied_acls = denied_acls or []

    def __str__(self):
        """
        String representation for TcpListener
        :return: str
        """
        return str(self.__dict__)

    def __repr__(self):
        return 'TcpListener(%s)' % str(self)

    def __eq__(self, other):
        return self.name == other.name and \
            self.bind == other.bind and \
            self.upstream == other.upstream and \
            self.allowed_acls == other.allowed_acls and \
            self.denied_acls == other.denied_acls
