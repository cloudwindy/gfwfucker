from hashlib import md5 as objmd5

__all__ = ['enc', 'dec', 'hash', 'pretty_hex']

def enc(b):
    return int.to_bytes(b, 4, 'big')

def dec(n):
    return int.from_bytes(n, 'big')

def hash(s):
    md5_obj = objmd5()
    md5_obj.update(s.encode())
    return md5_obj.digest()

def pretty_hex(s):
    ' '.join('{:02x}'.format(ord(c)) for c in s)