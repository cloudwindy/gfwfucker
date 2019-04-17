from hashlib import md5 as objmd5

__all__ = ['enc', 'dec', 'md5']

def enc(b):
    return int.to_bytes(b, 4, 'big')
def dec(n):
    return int.from_bytes(n, 'big')
def md5(s):
    md5_obj = objmd5()
    md5_obj.update(s.encode())
    return md5_obj.digest()