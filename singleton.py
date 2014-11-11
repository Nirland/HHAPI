"""
Decorator singleton implementation
"""


def singleton(klass):
    instances = {}

    def get_instance(*arg, **kwarg):
        if (instances.get(klass, None) is None):
            instances[klass] = klass(*arg, **kwarg)
        return instances[klass]

    return get_instance
