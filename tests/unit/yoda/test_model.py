from nose.tools import eq_
from yoda import Location


def test_location_eq():
    """
    Should return true when two locations are equivalent.
    """

    # Given: Existing locations
    loc1 = Location('upstream1')
    loc2 = Location('upstream1')

    # When: I compare two locations
    result = loc1 == loc2

    # Then: Two locations are equivalent
    eq_(result, True)
