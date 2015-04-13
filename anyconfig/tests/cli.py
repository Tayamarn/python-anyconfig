#
# Copyright (C) 2013 Satoru SATOH <ssato @ redhat.com>
# License: MIT
#
import os
import os.path
import subprocess
import sys
import unittest

import anyconfig.cli as TT
import anyconfig.api as A
import anyconfig.template
import anyconfig.tests.common as C


def run(args=[]):
    """
    It will throw subprocess.CalledProcessError if something goes wrong.
    """
    args = ["python", os.path.join(C.selfdir(), "..", "cli.py")] + args
    devnull = open('/dev/null', 'w')

    subprocess.check_call(args, stdout=devnull, stderr=devnull)


class Test_10_effectful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()
        self.script = os.path.join(C.selfdir(), "..", "cli.py")

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def run_and_check_exit_code(self, args=[], code=0, _not=False):
        try:
            TT.main(["dummy"] + args)
        except SystemExit as e:
            if _not:
                self.assertNotEquals(e.code, code)
            else:
                self.assertEquals(e.code, code)

    def test_10__show_usage(self):
        run(["--help"])

    def test_12__wrong_option(self):
        self.run_and_check_exit_code(["--wrong-option-xyz"], _not=True)

    def test_20__list(self):
        run(["--list"])

    def test_22__list(self):
        self.run_and_check_exit_code(["--list"])

    def test_30_single_input(self):
        a = dict(name="a", a=1, b=dict(b=[1, 2], c="C"))

        input = os.path.join(self.workdir, "a.json")
        output = os.path.join(self.workdir, "b.json")

        A.dump(a, input)
        self.assertTrue(os.path.exists(input))

        TT.main(["dummy", "-o", output, input])
        self.assertTrue(os.path.exists(output))

    def test_32_single_input_w_get_option(self):
        d = dict(name="a", a=dict(b=dict(c=[1, 2], d="C")))

        input = os.path.join(self.workdir, "a.json")
        output = os.path.join(self.workdir, "b.json")

        A.dump(d, input)
        self.assertTrue(os.path.exists(input))

        TT.main(["dummy", "-o", output, "--get", "a.b", input])
        self.assertTrue(os.path.exists(output))

        x = A.load(output)
        self.assertEquals(x, d['a']['b'])

    def test_34_single_input_w_set_option(self):
        d = dict(name="a", a=dict(b=dict(c=[1, 2], d="C")))

        input = os.path.join(self.workdir, "a.json")
        output = os.path.join(self.workdir, "b.json")

        A.dump(d, input)
        self.assertTrue(os.path.exists(input))

        TT.main(["dummy", "-o", output, "--set", "a.b.d=E", input])
        self.assertTrue(os.path.exists(output))

        ref = d.copy()
        ref['a']['b']['d'] = 'E'

        x = A.load(output)
        self.assertEquals(x, ref)

    def test_36_single_input__ignore_missing(self):
        # null_cntnr = A.container()
        input = os.path.join(os.curdir, "conf_file_should_not_exist.json")
        assert not os.path.exists(input)

        TT.main(["dummy", "-O", "json", "--ignore-missing",
                input])

    def test_40_multiple_inputs(self):
        xs = [dict(a=1, ),
              dict(b=dict(b=[1, 2], c="C")), ]

        a = xs[0].copy()
        a.update(xs[1])

        output = os.path.join(self.workdir, "b.json")

        inputs = []
        for i in [0, 1]:
            input = os.path.join(self.workdir, "a%d.json" % i)
            inputs.append(input)

            A.dump(xs[i], input)
            self.assertTrue(os.path.exists(input))

        TT.main(["dummy", "-o", output] + inputs)
        self.assertTrue(os.path.exists(output))

    def test_50_single_input__w_arg_option(self):
        a = dict(name="a", a=1, b=dict(b=[1, 2], c="C"), d=[1, 2])

        input = os.path.join(self.workdir, "a.json")
        output = os.path.join(self.workdir, "b.json")

        A.dump(a, input)
        self.assertTrue(os.path.exists(input))

        TT.main(["dummy", "-o", output, "-A", "a:10;name:x;d:3,4", input])
        self.assertTrue(os.path.exists(output))

        x = A.load(output)

        self.assertNotEquals(a["name"], x["name"])
        self.assertNotEquals(a["a"], x["a"])
        self.assertNotEquals(a["d"], x["d"])

        self.assertEquals(x["name"], 'x')
        self.assertEquals(x["a"], 10)
        self.assertEquals(x["d"], [3, 4])

    def test_60_output_wo_output_option_w_otype(self):
        a = dict(name="a", a=1, b=dict(b=[1, 2], c="C"))
        input = os.path.join(self.workdir, "a.json")
        A.dump(a, input)

        self.run_and_check_exit_code(["--otype", "json", input], 0)

    def test_62_output_wo_output_option_and_otype_w_itype(self):
        a = dict(name="a", a=1, b=dict(b=[1, 2], c="C"))
        input = os.path.join(self.workdir, "a.json")
        A.dump(a, input)

        self.run_and_check_exit_code(["--itype", "json", input], 0)

    def test_70_multi_inputs__w_template(self):
        if not anyconfig.template.SUPPORTED:
            return

        a = dict(name="a", a=1, b=dict(b=[1, 2], c="C"))

        inputsdir = os.path.join(self.workdir, "in")
        os.makedirs(inputsdir)

        A.dump(a, os.path.join(inputsdir, "a0.yml"))
        open(os.path.join(inputsdir, "a1.yml"), 'w').write("""\
name: {{ name }}
a: {{ a }}
b:
    b:
        {% for x in b.b -%}
        - {{ x }}
        {% endfor %}
    c: {{ b.c }}
""")

        output = os.path.join(self.workdir, "b.json")

        TT.main(["dummy", "-o", output,
                 os.path.join(inputsdir, "*.yml")])
        self.assertTrue(os.path.exists(output))

    def test_72_single_input__no_template(self):
        a = dict(name="a", a=1, b=dict(b=[1, 2], c="C"))

        input = os.path.join(self.workdir, "a.json")
        output = os.path.join(self.workdir, "b.json")

        A.dump(a, input)
        self.assertTrue(os.path.exists(input))

        TT.main(["dummy", "--no-template", "-o", output, input])
        self.assertTrue(os.path.exists(output))

    def test_74_multi_inputs__w_template(self):
        if not anyconfig.template.SUPPORTED:
            return

        curdir = C.selfdir()

        input = os.path.join(curdir, "*template-c*.yml")
        output = os.path.join(self.workdir, "output.yml")

        TT.main(["dummy", "-o", output, input])

    def test_80_no_out_dumper(self):
        a = dict(name="a", a=1, b=dict(b=[1, 2], c="C"), d=[1, 2])
        input = os.path.join(self.workdir, "a.json")
        A.dump(a, input)

        try:
            TT.main(["dummy", "-o", "out.txt", input])
            sys.exit(-1)
        except RuntimeError:
            pass

    def test_82_no_itype_and_otype(self):
        try:
            TT.main(["dummy", "-o", "out.txt", "in.txt"])
            sys.exit(-1)
        except RuntimeError:
            pass

# vim:sw=4:ts=4:et:
