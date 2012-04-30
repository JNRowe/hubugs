from os import getenv

from nose.plugins.skip import SkipTest


def skip_check(f):
    def wrapper(*args):
        if getenv('TRAVIS'):
            raise SkipTest("Test %s is skipped" % f.__name__)
        else:
            return f(*args)
    wrapper.__name__ = f.__name__
    return wrapper
