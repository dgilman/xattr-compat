# Copyright 2021 David Gilman
# Licensed under the MIT license. See LICENSE for details.

import os
import os.path
import platform
import tempfile
import unittest

import xattr_compat

PLAT = platform.system()
TMPDIR = os.environ.get("TMPDIR")


class TestLibcXattr(unittest.TestCase):
    KEY = "user.test_key"
    VALUE = b"test_value"
    VALUE_WITH_NULLS = b"test\0value"

    def setUp(self) -> None:
        self.test_file = tempfile.NamedTemporaryFile(dir=TMPDIR)

    def tearDown(self) -> None:
        self.test_file.close()

    def test_smoke(self):
        test_dir = os.path.dirname(self.test_file.name)
        test_dir_fd = os.open(test_dir, os.O_RDONLY)

        smoke_tests = [
            ("file by name", self.test_file.name),
            ("file by fd", self.test_file.fileno()),
            ("dir by name", test_dir),
            ("dir by fd", test_dir_fd),
        ]

        for subtest_desc, subtest in smoke_tests:
            with self.subTest(subtest_desc):
                xattr_compat.setxattr(subtest, self.KEY, self.VALUE)
                self.assertEqual(xattr_compat.getxattr(subtest, self.KEY), self.VALUE)
                self.assertTrue(self.KEY in xattr_compat.listxattr(subtest))
                xattr_compat.removexattr(subtest, self.KEY)
                self.assertTrue(self.KEY not in xattr_compat.listxattr(subtest))

        os.close(test_dir_fd)

    @unittest.skipIf(PLAT != "Darwin", "tests NOFOLLOW behavior only on Darwin")
    def test_nofollow_symlinks_fd(self):
        # Darwin doesn't demand that NOFOLLOW and file descriptor mode are incompatible
        xattr_compat.setxattr(
            self.test_file.fileno(), self.KEY, self.VALUE, follow_symlinks=False
        )
        self.assertEqual(
            xattr_compat.getxattr(
                self.test_file.fileno(), self.KEY, follow_symlinks=False
            ),
            self.VALUE,
        )

    def test_null_value(self):
        xattr_compat.setxattr(self.test_file.name, self.KEY, self.VALUE_WITH_NULLS)
        self.assertEqual(
            xattr_compat.getxattr(self.test_file.name, self.KEY), self.VALUE_WITH_NULLS
        )

    def test_zero_length_xattr(self):
        xattr_compat.setxattr(self.test_file.name, self.KEY, b"")
        self.assertEqual(xattr_compat.getxattr(self.test_file.name, self.KEY), b"")

    def test_list_zero_attr(self):
        self.assertEqual(xattr_compat.listxattr(self.test_file.name), [])

    def test_list_many_attr(self):
        attrs = ["foo", "bar", "baz"]
        for attr in attrs:
            xattr_compat.setxattr(self.test_file.name, attr, b"")
        # Darwin doesn't guarantee the order of attr names and appears to use a stack
        # to store them.
        self.assertEqual(
            sorted(xattr_compat.listxattr(self.test_file.name)), sorted(attrs)
        )


class TextXattrs(unittest.TestCase):
    KEY = "user.test_key"
    VALUE = b"test_value"
    VALUE_WITH_NULLS = b"test\0value"

    def setUp(self) -> None:
        self.test_file = tempfile.NamedTemporaryFile(dir=TMPDIR)
        self.xattrs = xattr_compat.Xattrs(self.test_file.name)

    def tearDown(self) -> None:
        self.test_file.close()

    def test_keys(self):
        self.assertEqual(self.xattrs.keys(), [])

    def test_len(self):
        self.assertEqual(len(self.xattrs), 0)

    def test_setitem(self):
        with self.assertRaises(TypeError):
            self.xattrs[42] = self.VALUE
        with self.assertRaises(TypeError):
            self.xattrs[self.KEY] = "asdfasdf"

        self.xattrs[self.KEY] = self.VALUE

    def test_getitem(self):
        self.assertRaises(TypeError, lambda: self.xattrs[42])
        self.assertRaises(KeyError, lambda: self.xattrs["swag"])

        self.xattrs[self.KEY] = self.VALUE
        self.assertEqual(self.xattrs[self.KEY], self.VALUE)

    def test_delitem(self):
        self.xattrs[self.KEY] = self.VALUE

        with self.assertRaises(TypeError):
            del self.xattrs[42]

        with self.assertRaises(KeyError):
            del self.xattrs["Afdsafdfad"]

        del self.xattrs[self.KEY]


# XXX review other operating system's xattrs to see if impl is portable
