#
# Copyright (C) 2012 - 2015 Satoru SATOH <ssato @ redhat.com>
# License: MIT
#
import os
import tempfile
import unittest

import anyconfig.backend.json_ as TT


CONF_0 = """{
  "a": 0,
  "b": "bbb",

  "sect0": {
    "c": ["x", "y", "z"]
  }
}
"""


class Test_JsonConfigParser(unittest.TestCase):

    def setUp(self):
        (_, conf) = tempfile.mkstemp(prefix="ac-test-")
        open(conf, 'w').write(CONF_0)
        self.config_path = conf

    def tearDown(self):
        os.remove(self.config_path)

    def test_00_supports(self):
        self.assertFalse(TT.JsonConfigParser.supports("/a/b/c/d.ini"))
        self.assertTrue(TT.JsonConfigParser.supports("/a/b/c/d.json"))

    def test_10_loads(self):
        c = TT.JsonConfigParser.loads(CONF_0)

        self.assertEquals(c['a'], 0, str(c))
        self.assertEquals(c['b'], "bbb", c)
        self.assertEquals(c['sect0']['c'], ['x', 'y', 'z'])

    def test_20_load(self):
        c = TT.JsonConfigParser.load(self.config_path)

        self.assertEquals(c['a'], 0, str(c))
        self.assertEquals(c['b'], "bbb", c)
        self.assertEquals(c['sect0']['c'], ['x', 'y', 'z'])

    def test_20_load__optional_kwargs(self):
        c = TT.JsonConfigParser.load(self.config_path, parse_int=None)

        self.assertEquals(c['a'], 0, str(c))
        self.assertEquals(c['b'], "bbb", c)
        self.assertEquals(c['sect0']['c'], ['x', 'y', 'z'])

    def test_30_dumps(self):
        c = TT.JsonConfigParser.loads(CONF_0)
        s = TT.JsonConfigParser.dumps(c)
        c = TT.JsonConfigParser.loads(s)

        self.assertEquals(c['a'], 0, str(c))
        self.assertEquals(c['b'], "bbb", c)
        self.assertEquals(c['sect0']['c'], ['x', 'y', 'z'])

    def test_40_dump(self):
        c = TT.JsonConfigParser.loads(CONF_0)
        TT.JsonConfigParser.dump(c, self.config_path)
        c = TT.JsonConfigParser.load(self.config_path)

        self.assertEquals(c['a'], 0, str(c))
        self.assertEquals(c['b'], "bbb", c)
        self.assertEquals(c['sect0']['c'], ['x', 'y', 'z'])

    def test_50_dump_w_backend_specific_options(self):
        c = TT.JsonConfigParser.loads(CONF_0)
        TT.JsonConfigParser.dump(c, self.config_path, parse_int=None,
                                 indent=3)
        c = TT.JsonConfigParser.load(self.config_path)

        self.assertEquals(c['a'], 0, str(c))
        self.assertEquals(c['b'], "bbb", c)
        self.assertEquals(c['sect0']['c'], ['x', 'y', 'z'])

# vim:sw=4:ts=4:et:
