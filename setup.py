# Copyright 2021 David Gilman
# Licensed under the MIT license. See LICENSE for details.

import pathlib

from setuptools import setup

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="xattr-compat",
    version="1.0.0",
    description="Multi-platform extended attributes support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dgilman/xattr_compat",
    author="David Gilman",
    author_email="davidgilman1@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: POSIX :: Linux",
        "Environment :: MacOS X",
        "Operating System :: POSIX :: BSD :: FreeBSD",
        "Operating System :: POSIX :: BSD :: NetBSD",
    ],
    packages=["xattr_compat"],
    python_requires=">=3.6",
    project_urls={
        "Bug Reports": "https://github.com/dgilman/xattr_compat/issues",
        "Source": "https://github.com/dgilman/xattr_compat/",
    },
)
