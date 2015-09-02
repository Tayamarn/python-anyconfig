#
# Copyright (C) 2012 - 2015 Satoru SATOH <ssato @ redhat.com>
# License: MIT
#
# pylint: disable=missing-docstring, protected-access
import os
import os.path
import unittest

import anyconfig.backend.base as TT  # stands for test target
import anyconfig.mergeabledict
import anyconfig.tests.common


class Test00(unittest.TestCase):

    def setUp(self):
        self.psr = TT.Parser()

    def test_10_type(self):
        self.assertEquals(self.psr.type(), TT.Parser._type)

    def test_20_loads__null_content(self):
        cnf = self.psr.loads('')
        self.assertEquals(cnf, self.psr.container())
        self.assertTrue(isinstance(cnf, self.psr.container))

    def test_30_load__ignore_missing(self):
        cpath = os.path.join(os.curdir, "conf_file_should_not_exist")
        assert not os.path.exists(cpath)

        cnf = self.psr.load(cpath, ignore_missing=True)
        self.assertEquals(cnf, self.psr.container())
        self.assertTrue(isinstance(cnf, self.psr.container))


class Test10(unittest.TestCase):

    def setUp(self):
        self.workdir = anyconfig.tests.common.setup_workdir()

    def tearDown(self):
        anyconfig.tests.common.cleanup_workdir(self.workdir)

    def test_10_ensure_outdir_exists(self):
        outdir = os.path.join(self.workdir, "outdir")
        outfile = os.path.join(outdir, "a.txt")

        TT.ensure_outdir_exists(outfile)

        self.assertTrue(os.path.exists(outdir))

# vim:sw=4:ts=4:et:
