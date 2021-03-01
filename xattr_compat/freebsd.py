# Copyright 2021 David Gilman
# Licensed under the MIT license. See LICENSE for details.

import ctypes
import ctypes.util
import os
from typing import List, Optional, Tuple, Union

# sys/xattr.h
EXTATTR_NAMESPACE_USER = 0x00000001
EXTATTR_NAMESPACE_SYSTEM = 0x00000002

PATH_LIKE = Union[os.PathLike, int, Tuple[int, str]]


libc_path = ctypes.util.find_library("c")

if libc_path is None:
    raise Exception("Unable to find path to libc")

libc = ctypes.CDLL(libc_path, use_errno=True)

try:
    c_extattr_get_fd = libc.extattr_get_fd
    c_extattr_set_fd = libc.extattr_set_fd
    c_extattr_delete_fd = libc.extattr_delete_fd
    c_extattr_list_fd = libc.extattr_list_fd
    c_extattr_get_file = libc.extattr_get_file
    c_extattr_set_file = libc.extattr_set_file
    c_extattr_delete_file = libc.extattr_delete_file
    c_extattr_list_file = libc.extattr_list_file
    c_extattr_get_link = libc.extattr_get_link
    c_extattr_set_link = libc.extattr_set_link
    c_extattr_delete_link = libc.extattr_delete_link
    c_extattr_list_link = libc.extattr_list_link
except AttributeError as exc:
    exc_msg = str(exc)
    if not exc_msg.startswith("Undefined symbol"):
        raise

    # Undefined symbol "asdfadfsfdas"
    import re

    match = re.search(r'"(.*)"', exc_msg)
    if not match:
        raise

    symbol_name = match.group(1)
    raise Exception(f"Unable to find symbol: {symbol_name}") from None


def _oserror():
    errno = ctypes.get_errno()
    raise OSError(errno, os.strerror(errno))


def _parse_path(path, str_fn, fd_fn, link_fn, follow_symlinks=True):
    if isinstance(path, tuple):
        if len(path) != 2:
            raise ValueError("Invalid path tuple")
        namespace, path = path
        if namespace not in (EXTATTR_NAMESPACE_SYSTEM, EXTATTR_NAMESPACE_USER):
            raise ValueError("Invalid extattr namespace")
    else:
        namespace = EXTATTR_NAMESPACE_USER

    if isinstance(path, int):
        fn = fd_fn
    else:
        path = os.fsencode(path)
        if follow_symlinks:
            fn = str_fn
        else:
            fn = link_fn
    return namespace, path, fn


c_extattr_get_fd.argtypes = [
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_get_fd.restype = ctypes.c_ssize_t
c_extattr_get_file.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_get_file.restype = ctypes.c_ssize_t
c_extattr_get_link.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_get_link.restype = ctypes.c_ssize_t


c_extattr_set_fd.argtypes = [
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_set_fd.restype = ctypes.c_ssize_t
c_extattr_set_file.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_set_file.restype = ctypes.c_ssize_t
c_extattr_set_link.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_set_link.restype = ctypes.c_ssize_t

c_extattr_delete_fd.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
c_extattr_delete_fd.restype = ctypes.c_int
c_extattr_delete_file.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
c_extattr_delete_file.restype = ctypes.c_int
c_extattr_delete_link.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
c_extattr_delete_link.restype = ctypes.c_int

c_extattr_list_fd.argtypes = [
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_list_fd.restype = ctypes.c_ssize_t
c_extattr_list_file.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_list_file.restype = ctypes.c_ssize_t
c_extattr_list_link.argtypes = [
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.c_size_t,
]
c_extattr_list_link.restype = ctypes.c_ssize_t


def setxattr(
    path: PATH_LIKE,
    attribute: str,
    value: bytes,
    flags: int = 0,
    *,
    follow_symlinks: bool = True,
):
    namespace, path, fn = _parse_path(
        path,
        c_extattr_set_file,
        c_extattr_set_fd,
        c_extattr_set_link,
        follow_symlinks=follow_symlinks,
    )
    attribute = os.fsencode(attribute)
    size = len(value)
    buf = ctypes.create_string_buffer(value)
    buf_ptr = ctypes.cast(ctypes.pointer(buf), ctypes.c_void_p)

    retval = fn(path, namespace, attribute, buf_ptr, size)

    if retval == size:
        return

    if retval < 0:
        _oserror()

    # XXX how should this error case be handled?
    raise Exception("Incomplete write")


def getxattr(path: PATH_LIKE, attribute: str, *, follow_symlinks: bool = True) -> bytes:

    namespace, path, fn = _parse_path(
        path,
        c_extattr_get_file,
        c_extattr_get_fd,
        c_extattr_get_link,
        follow_symlinks=follow_symlinks,
    )
    attribute = os.fsencode(attribute)

    attr_size = fn(path, namespace, attribute, None, 0)

    if attr_size < 0:
        _oserror()

    buf = ctypes.create_string_buffer(attr_size)
    buf_ptr = ctypes.cast(ctypes.pointer(buf), ctypes.c_void_p)
    retval = fn(path, namespace, attribute, buf_ptr, attr_size)

    if retval != attr_size:
        _oserror()

    return buf.raw


def listxattr(path: Optional[PATH_LIKE], *, follow_symlinks: bool = True) -> List[str]:
    if path is None:
        path = "."

    namespace, path, fn = _parse_path(
        path,
        c_extattr_list_file,
        c_extattr_list_fd,
        c_extattr_list_link,
        follow_symlinks=follow_symlinks,
    )

    buf_size = fn(path, namespace, None, 0)

    if buf_size < 0:
        _oserror()

    if buf_size == 0:
        return []

    buf = ctypes.create_string_buffer(buf_size)
    buf_ptr = ctypes.cast(ctypes.pointer(buf), ctypes.c_char_p)
    retval = fn(path, namespace, buf_ptr, buf_size)

    if retval != buf_size:
        _oserror()

    data = memoryview(buf.raw)
    attrs = []
    while data:
        attr_len = data[0]
        attrs.append(os.fsdecode(bytes(data[1 : attr_len + 1])))
        data = data[attr_len + 1 :]
    return attrs


def removexattr(path: PATH_LIKE, attribute: str, *, follow_symlinks: bool = True):
    namespace, path, fn = _parse_path(
        path,
        c_extattr_delete_file,
        c_extattr_delete_fd,
        c_extattr_delete_link,
        follow_symlinks=follow_symlinks,
    )
    attribute = os.fsencode(attribute)

    retval = fn(path, namespace, attribute)

    if retval == 0:
        return

    _oserror()
