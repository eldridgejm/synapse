import collections


def get_key_parts(k):
    KeyParts = collections.namedtuple('KeyParts', 'type name')
    parts = k.split(':')
    if len(parts) > 1:
        return KeyParts(*parts)
    else:
        return KeyParts('topic', k)
