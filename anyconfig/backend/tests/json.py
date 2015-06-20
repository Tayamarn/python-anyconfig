#
# Copyright (C) 2012 - 2015 Satoru SATOH <ssato @ redhat.com>
# License: MIT
#
# pylint: disable=missing-docstring
import os.path
import unittest

import anyconfig.backend.json as TT
import anyconfig.tests.common


CONF_0 = """{
  "a": 0,
  "b": "bbb",

  "sect0": {
    "c": ["x", "y", "z"]
  }
}
"""


class Test(unittest.TestCase):

    def setUp(self):
        self.workdir = anyconfig.tests.common.setup_workdir()
        self.cpath = os.path.join(self.workdir, "test0.json")
        open(self.cpath, 'w').write(CONF_0)

    def tearDown(self):
        anyconfig.tests.common.cleanup_workdir(self.workdir)

    def test_00_supports(self):
        self.assertFalse(TT.Parser.supports("/a/b/c/d.ini"))
        self.assertTrue(TT.Parser.supports("/a/b/c/d.json"))

    def test_10_loads(self):
        cfg = TT.Parser.loads(CONF_0)

        self.assertEquals(cfg['a'], 0, str(cfg))
        self.assertEquals(cfg['b'], "bbb", cfg)
        self.assertEquals(cfg['sect0']['c'], ['x', 'y', 'z'])

    def test_20_load(self):
        cfg = TT.Parser.load(self.cpath)

        self.assertEquals(cfg['a'], 0, str(cfg))
        self.assertEquals(cfg['b'], "bbb", cfg)
        self.assertEquals(cfg['sect0']['c'], ['x', 'y', 'z'])

    def test_22_load__optional_kwargs(self):
        cfg = TT.Parser.load(self.cpath, parse_int=None)

        self.assertEquals(cfg['a'], 0, str(cfg))
        self.assertEquals(cfg['b'], "bbb", cfg)
        self.assertEquals(cfg['sect0']['c'], ['x', 'y', 'z'])

    def test_30_dumps(self):
        cfg = TT.Parser.loads(CONF_0)
        cfg2 = TT.Parser.loads(TT.Parser.dumps(cfg))

        self.assertEquals(cfg2['a'], 0, str(cfg))
        self.assertEquals(cfg2['b'], "bbb", cfg)
        self.assertEquals(cfg2['sect0']['c'], ['x', 'y', 'z'])

    def test_40_dump(self):
        cfg = TT.Parser.loads(CONF_0)
        TT.Parser.dump(cfg, self.cpath)
        cfg = TT.Parser.load(self.cpath)

        self.assertEquals(cfg['a'], 0, str(cfg))
        self.assertEquals(cfg['b'], "bbb", cfg)
        self.assertEquals(cfg['sect0']['c'], ['x', 'y', 'z'])

    def test_42_dump_w_special_option(self):
        cfg = TT.Parser.loads(CONF_0)
        TT.Parser.dump(cfg, self.cpath, parse_int=None, indent=3)
        cfg = TT.Parser.load(self.cpath)

        self.assertEquals(cfg['a'], 0, str(cfg))
        self.assertEquals(cfg['b'], "bbb", cfg)
        self.assertEquals(cfg['sect0']['c'], ['x', 'y', 'z'])

# vim:sw=4:ts=4:et:
