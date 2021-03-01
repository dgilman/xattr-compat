# xattr-compat

Support for extended attributes on multiple platforms. Also includes a mutable mapping class for easy access to file xattrs.

No C modules have to be compiled to use this library and it has no dependencies. The ctypes module in the standard library is used to make the required libc calls. Performance should be fine for all purposes. I mean, it's just xattrs, who is making so many xattr calls from Python that they need something above and beyond this?

## Usage

The package exports the `getxattr`, `listxattr`, `removexattr` and `setxattr` functions. They have identical function signatures to the [versions implemented in the os module in the standard library.](https://docs.python.org/3/library/os.html#linux-extended-attributes)

There's also a class `Xattrs` that provides a simple mutable mapping over a file's extended attributes:

```python
# class Xattrs(path: os.PathLike, follow_symlinks: bool = True)

import xattr_compat

xattrs = xattr_compat.Xattrs("./my_file")

xattrs["user.humanfund.xattr"] = b"hello\0world"

print("Extended attributes:", xattrs.items())
```

## License

MIT

## Sponsorship

Development of xattr-compat is sponsored by [Pro Football History.com, your source for NFL coaching biographies.](https://pro-football-history.com)