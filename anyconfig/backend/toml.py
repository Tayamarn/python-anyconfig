#
# Copyright (C) 2015 Satoru SATOH <ssato @ redhat.com>
# License: MIT
#
# Ref. python -c "import toml; help(toml); ..."
#
# pylint: disable=unused-argument
"""TOML backend.

.. versionadded:: 0.1.0

- Format to support: TOML, https://github.com/toml-lang/toml
- Requirements: (python) toml module, https://github.com/uiri/toml
- Limitations: None obvious
- Special options:

  - toml.{load{s,},dump{s,}} only accept '_dict' keyword option but it's not
    supported and will be ignored.
"""
from __future__ import absolute_import

import functools
import toml
import anyconfig.backend.json


def call_with_no_kwargs(func):
    """
    Call :func:`func` without given keyword args

    :param func: Any callable object

    >>> call_with_no_kwargs(len)([], kwarg0_ignored=True)
    0
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapper function.
        """
        return func(*args)

    return wrapper


class Parser(anyconfig.backend.json.Parser):
    """
    TOML parser.
    """
    _type = "toml"
    _extensions = ["toml"]
    _funcs = dict(loads=call_with_no_kwargs(toml.loads),
                  load=call_with_no_kwargs(toml.load),
                  dumps=call_with_no_kwargs(toml.dumps),
                  dump=call_with_no_kwargs(toml.dump))

# vim:sw=4:ts=4:et:
