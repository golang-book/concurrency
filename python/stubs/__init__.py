"""
The stubs here acompany http://www.doxsey.net/blog/go-concurrency-from-the-ground-up
"""


# Scheduling Methods


def go(callback):
    pass


def run():
    pass


# Channel Methods


class Channel:
    pass

def make():
    return Channel()


def len(channel):
    return 0


def cap(channel):
    return 0


def send(channel, value, callback):
    pass


def recv(channel, callback):
    pass


def close(channel):
    pass


# Selection


def select(cases, callback=None):
    pass
