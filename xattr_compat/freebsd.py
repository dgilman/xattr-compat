# Copyright 2021 David Gilman
# Licensed under the MIT license. See LICENSE for details.

import ctypes
import ctypes.util
import errno
import os
from typing import List, Optional

# sys/xattr.h
XATTR_NOFOLLOW = 0x0001
XATTR_CREATE = 0x0002
XATTR_REPLACE = 0x0004
XATTR_NOSECURITY = 0x0008
XATTR_NODEFAULT = 0x0010
XATTR_SHOWCOMPRESSION = 0x0020
XATTR_MAXNAMELEN = 127
XATTR_FINDERINFO_NAME = "com.apple.FinderInfo"
XATTR_RESOURCEFORK_NAME = "com.apple.ResourceFork"

MISSING_KEY_ERRNO = errno.ENOATTR

libc_path = ctypes.util.find_library("c")

if libc_path is None:
    raise Exception("Unable to find path to libc")

libc = ctypes.CDLL(libc_path, use_errno=True)

try:
    c_getxattr = libc.getxattr
    c_fgetxattr = libc.fgetxattr
    c_listxattr = libc.listxattr
    c_flistxattr = libc.flistxattr
    c_removexattr = libc.removexattr
    c_fremovexattr = libc.fremovexattr
    c_setxattr = libc.setxattr
    c_fsetxattr = libc.fsetxattr
except AttributeError as exc:
    exc_msg = str(exc)
    if not exc_msg.endswith("symbol not found"):
        raise

    # dlsym(0x111dde8b0, asdfasfd): symbol not found
    import re

    match = re.search(r"[(].*, (.*)[)]", exc_msg)
    if not match:
        raise

    symbol_name = match.group(1)
    raise Exception(f"Unable to find symbol: {symbol_name}") from None


def _oserror():
    errno = ctypes.get_errno()
    raise OSError(errno, os.strerror(errno))


def _parse_path(path, str_fn, fd_fn):
    if isinstance(path, int):
        fn = fd_fn
    else:
        path = os.fsencode(path)
        fn = str_fn
    return path, fn


c_setxattr.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.c_int,
]
c_setxattr.restype = ctypes.c_int
c_fsetxattr.argtypes = [
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.c_int,
]
c_fsetxattr.restype = ctypes.c_int


def setxattr(
    path: os.PathLike,
    attribute: str,
    value: bytes,
    flags: int = 0,
    *,
    follow_symlinks: bool = True,
):
    if not follow_symlinks:
        flags = flags & XATTR_NOFOLLOW

    path, fn = _parse_path(path, c_setxattr, c_fsetxattr)
    attribute = attribute.encode("UTF-8")
    size = len(value)
    buf = ctypes.create_string_buffer(value)
    buf_ptr = ctypes.cast(ctypes.pointer(buf), ctypes.c_void_p)

    retval = fn(path, attribute, buf_ptr, size, 0, flags)

    if retval == 0:
        return

    _oserror()


c_getxattr.argtypes = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.c_int,
]
c_getxattr.restype = ctypes.c_ssize_t
c_fgetxattr.argtypes = [
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_uint32,
    ctypes.c_int,
]
c_fgetxattr.restype = ctypes.c_ssize_t


def getxattr(
    path: os.PathLike, attribute: str, *, follow_symlinks: bool = True
) -> bytes:
    flags = 0
    if not follow_symlinks:
        flags = flags & XATTR_NOFOLLOW

    path, fn = _parse_path(path, c_getxattr, c_fgetxattr)
    attribute = attribute.encode("UTF-8")

    attr_size = fn(path, attribute, None, 0, 0, flags)

    if attr_size < 0:
        _oserror()

    buf = ctypes.create_string_buffer(attr_size)
    buf_ptr = ctypes.cast(ctypes.pointer(buf), ctypes.c_void_p)
    retval = fn(path, attribute, buf_ptr, attr_size, 0, flags)

    if retval != attr_size:
        _oserror()

    return buf.raw


c_listxattr.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
c_listxattr.restype = ctypes.c_ssize_t
c_flistxattr.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
c_flistxattr.restype = ctypes.c_ssize_t


def listxattr(
    path: Optional[os.PathLike], *, follow_symlinks: bool = True
) -> List[str]:
    if path is None:
        path = "."

    flags = 0
    if not follow_symlinks:
        flags = flags & XATTR_NOFOLLOW

    path, fn = _parse_path(path, c_listxattr, c_flistxattr)

    buf_size = fn(path, None, 0, flags)

    if buf_size < 0:
        _oserror()

    if buf_size == 0:
        return []

    buf = ctypes.create_string_buffer(buf_size)
    buf_ptr = ctypes.cast(ctypes.pointer(buf), ctypes.c_char_p)
    retval = fn(path, buf_ptr, buf_size, flags)

    if retval != buf_size:
        _oserror()

    return [attr.decode("UTF-8") for attr in buf.raw.split(b"\0")][:-1]


c_removexattr.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
c_removexattr.restype = ctypes.c_int
c_fremovexattr.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
c_fremovexattr.restype = ctypes.c_int


def removexattr(path: os.PathLike, attribute: str, *, follow_symlinks: bool = True):
    flags = 0
    if not follow_symlinks:
        flags = flags & XATTR_NOFOLLOW

    path, fn = _parse_path(path, c_removexattr, c_fremovexattr)
    attribute = attribute.encode("UTF-8")

    retval = fn(path, attribute, flags)

    if retval == 0:
        return

    _oserror()
