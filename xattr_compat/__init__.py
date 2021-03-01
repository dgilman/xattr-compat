# Copyright 2021 David Gilman
# Licensed under the MIT license. See LICENSE for details.

import collections.abc
import errno
import os
import platform
from typing import Iterator, List

_sys = platform.system()
__all__ = ["Xattrs", "setxattr", "getxattr", "listxattr", "removexattr"]

if _sys == "Darwin":
    from .darwin import *

    KEY_TYPES = str
    MISSING_KEY_ERRNO = errno.ENOATTR

    __all__ += [
        "XATTR_NOFOLLOW",
        "XATTR_CREATE",
        "XATTR_REPLACE",
        "XATTR_NOSECURITY",
        "XATTR_NODEFAULT",
        "XATTR_SHOWCOMPRESSION",
        "XATTR_MAXNAMELEN",
        "XATTR_FINDERINFO_NAME",
        "XATTR_FINDERINFO_NAME",
        "XATTR_RESOURCEFORK_NAME",
    ]
elif _sys == "Linux":
    from os import (
        XATTR_CREATE,
        XATTR_REPLACE,
        XATTR_SIZE_MAX,
        getxattr,
        listxattr,
        removexattr,
        setxattr,
    )

    KEY_TYPES = str
    MISSING_KEY_ERRNO = errno.ENODATA

    __all__ += ["XATTR_SIZE_MAX", "XATTR_CREATE", "XATTR_REPLACE"]
elif _sys in ("FreeBSD", "NetBSD"):
    from .freebsd import *

    KEY_TYPES = (str, tuple)
    MISSING_KEY_ERRNO = errno.ENOATTR

    __all__ += ["EXTATTR_NAMESPACE_USER", "EXTATTR_NAMESPACE_SYSTEM"]
else:
    raise Exception(f"Unknown platform {_sys}")


class Xattrs(collections.abc.MutableMapping):
    def __init__(self, path: os.PathLike, follow_symlinks: bool = True):
        self.path = path
        self.follow_symlinks = follow_symlinks

    def __repr__(self):
        return f"<Xattrs path={repr(self.path)}>"

    def keys(self) -> List[str]:
        return listxattr(self.path, follow_symlinks=self.follow_symlinks)

    def __len__(self) -> int:
        return len(self.keys())

    def __getitem__(self, k: str) -> bytes:
        if not isinstance(k, KEY_TYPES):
            raise TypeError(f"Xattr keys must be str, not {type(k).__name__}")

        try:
            return getxattr(self.path, k, follow_symlinks=self.follow_symlinks)
        except OSError as e:
            if e.errno == MISSING_KEY_ERRNO:
                raise KeyError(k) from None
            raise

    def __setitem__(self, k: str, v: bytes) -> None:
        if not isinstance(k, KEY_TYPES):
            raise TypeError(f"Xattr keys must be str, not {type(k).__name__}")
        if not isinstance(v, bytes):
            raise TypeError(f"Xattr values must be bytes, not {type(k).__name__}")

        return setxattr(self.path, k, v, follow_symlinks=self.follow_symlinks)

    def __delitem__(self, k: str) -> None:
        if not isinstance(k, KEY_TYPES):
            raise TypeError(f"Xattr keys must be str, not {type(k).__name__}")

        try:
            removexattr(self.path, k, follow_symlinks=self.follow_symlinks)
        except OSError as e:
            if e.errno == MISSING_KEY_ERRNO:
                raise KeyError(k) from None
            raise

    def __iter__(self) -> Iterator[str]:
        return iter(self.keys())
