#
# Copyright (C) 2012 - 2015 Satoru SATOH <ssato @ redhat.com>
# License: MIT
#
# pylint: disable=missing-docstring
import random
import unittest

import anyconfig.backend.backends as TT
import anyconfig.backend.ini_
import anyconfig.backend.json_

try:
    import anyconfig.backend.yaml_
    YAML_FOUND = True
except ImportError:
    YAML_FOUND = False


class Test(unittest.TestCase):

    def test_10_find_by_file(self):
        ini_cf = "/a/b/c.ini"
        unknown_cf = "/a/b/c.xyz"
        jsn_cfs = ["/a/b/c.jsn", "/a/b/c.json", "/a/b/c.js"]
        yml_cfs = ["/a/b/c.yml", "/a/b/c.yaml"]

        self.assertTrue(TT.find_by_file(unknown_cf) is None)
        self.assertEquals(TT.find_by_file(ini_cf),
                          anyconfig.backend.ini_.IniConfigParser)

        for cfg in jsn_cfs:
            self.assertEquals(TT.find_by_file(cfg),
                              anyconfig.backend.json_.JsonConfigParser)

        if YAML_FOUND:
            for cfg in yml_cfs:
                self.assertEquals(TT.find_by_file(cfg),
                                  anyconfig.backend.yaml_.YamlConfigParser)

    def test_20_find_by_type(self):
        ini_t = "ini"
        jsn_t = "json"
        yml_t = "yaml"
        unknown_t = "unknown_type"

        self.assertTrue(TT.find_by_type(unknown_t) is None)
        self.assertEquals(TT.find_by_type(ini_t),
                          anyconfig.backend.ini_.IniConfigParser)
        self.assertEquals(TT.find_by_type(jsn_t),
                          anyconfig.backend.json_.JsonConfigParser)

        if YAML_FOUND:
            self.assertEquals(TT.find_by_type(yml_t),
                              anyconfig.backend.yaml_.YamlConfigParser)

    def test_30_list_types(self):
        types = TT.list_types()

        self.assertTrue(isinstance(types, list))
        self.assertTrue(bool(list))  # ensure it's not empty.

    def test_40_cmp_cps(self):
        cps = TT.PARSERS
        if cps:
            res = TT.cmp_cps(random.choice(cps), random.choice(cps))
            self.assertTrue(res in (-1, 0, 1))

# vim:sw=4:ts=4:et:
