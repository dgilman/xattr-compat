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
        self.test_dir = tempfile.TemporaryDirectory(dir=TMPDIR)
        self.test_dir_fd = os.open(self.test_dir.name, os.O_RDONLY)
        self.test_file = tempfile.NamedTemporaryFile(dir=TMPDIR)

    def tearDown(self) -> None:
        self.test_file.close()
        os.close(self.test_dir_fd)
        self.test_dir.cleanup()

    def test_smoke(self):
        smoke_tests = [
            ("file by name", self.test_file.name),
            ("file by fd", self.test_file.fileno()),
            ("dir by name", self.test_dir.name),
            ("dir by fd", self.test_dir_fd),
        ]

        for subtest_desc, subtest in smoke_tests:
            with self.subTest(subtest_desc):
                xattr_compat.setxattr(subtest, self.KEY, self.VALUE)
                self.assertEqual(xattr_compat.getxattr(subtest, self.KEY), self.VALUE)
                self.assertTrue(self.KEY in xattr_compat.listxattr(subtest))
                xattr_compat.removexattr(subtest, self.KEY)
                self.assertTrue(self.KEY not in xattr_compat.listxattr(subtest))

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
        attrs = ["user.foo", "user.bar", "user.baz"]
        for attr in attrs:
            xattr_compat.setxattr(self.test_file.name, attr, b"")
        # Darwin doesn't guarantee the order of attr names and appears to use a stack
        # to store them.
        self.assertEqual(
            sorted(xattr_compat.listxattr(self.test_file.name)), sorted(attrs)
        )

    @unittest.skipIf(PLAT != "FreeBSD", "Namespace tuple only used on FreeBSD")
    def test_freebsd_namespaces(self):
        xattr_compat.setxattr(
            (xattr_compat.EXTATTR_NAMESPACE_USER, self.test_file.name),
            self.KEY,
            self.VALUE,
        )
        self.assertTrue(
            self.KEY
            not in xattr_compat.listxattr(
                (xattr_compat.EXTATTR_NAMESPACE_SYSTEM, self.test_file.name)
            )
        )


class TestXattrSymlinks(unittest.TestCase):
    KEY = "user.test_key"
    VALUE = b"test_value"

    def setUp(self) -> None:
        self.test_dir = tempfile.TemporaryDirectory(dir=TMPDIR)
        self.test_dir_fd = os.open(self.test_dir.name, os.O_RDONLY)
        self.test_file = tempfile.NamedTemporaryFile(dir=TMPDIR)
        self.test_symlink_name = self.test_file.name + "-link"
        os.symlink(self.test_file.name, self.test_symlink_name)
        self.test_dir_symlink_name = os.path.join(self.test_dir.name, "dir_symlink")
        os.symlink(self.test_dir.name, self.test_dir_symlink_name)

    def tearDown(self) -> None:
        os.remove(self.test_symlink_name)
        self.test_file.close()
        os.close(self.test_dir_fd)
        self.test_dir.cleanup()

    def test_nofollow_symlink(self):
        xattr_compat.setxattr(self.test_file.name, self.KEY, self.VALUE)
        xattr_compat.setxattr(self.test_dir.name, self.KEY, self.VALUE)

        self.assertTrue(
            self.KEY
            in xattr_compat.listxattr(self.test_symlink_name, follow_symlinks=True)
        )
        self.assertTrue(
            self.KEY
            in xattr_compat.listxattr(self.test_dir_symlink_name, follow_symlinks=True)
        )
        self.assertFalse(
            self.KEY
            in xattr_compat.listxattr(self.test_symlink_name, follow_symlinks=False)
        )
        self.assertFalse(
            self.KEY
            in xattr_compat.listxattr(self.test_dir_symlink_name, follow_symlinks=False)
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
        self.assertRaises(KeyError, lambda: self.xattrs["user.swag"])

        self.xattrs[self.KEY] = self.VALUE
        self.assertEqual(self.xattrs[self.KEY], self.VALUE)

    def test_delitem(self):
        self.xattrs[self.KEY] = self.VALUE

        with self.assertRaises(TypeError):
            del self.xattrs[42]

        with self.assertRaises(KeyError):
            del self.xattrs["user.Afdsafdfad"]

        del self.xattrs[self.KEY]
