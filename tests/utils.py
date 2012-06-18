from os import getenv


class HostError(EnvironmentError):
    """Error to raise when test can not be run on given host"""


def skip_check(f):
    def wrapper(*args):
        if getenv('TRAVIS'):
            raise HostError("Test %s is skipped" % f.__name__)
        else:
            return f(*args)
    wrapper.__name__ = f.__name__
    return wrapper
