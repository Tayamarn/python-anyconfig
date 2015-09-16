#
# Author: Satoru SATOH <ssato redhat.com>
# License: MIT
#
"""CLI frontend module for anyconfig.
"""
from __future__ import absolute_import

import codecs
import locale
import logging
import optparse
import os
import sys

import anyconfig.api as A
import anyconfig.compat
import anyconfig.globals
import anyconfig.mergeabledict
import anyconfig.parser


_ENCODING = locale.getdefaultlocale()[1]
A.LOGGER.addHandler(logging.StreamHandler())

if anyconfig.compat.IS_PYTHON_3:
    import io

    _ENCODING = _ENCODING.lower()

    # TODO: What should be done for an error, "AttributeError: '_io.StringIO'
    # object has no attribute 'buffer'"?
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=_ENCODING)
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=_ENCODING)
    except AttributeError:
        pass
else:
    sys.stdout = codecs.getwriter(_ENCODING)(sys.stdout)
    sys.stderr = codecs.getwriter(_ENCODING)(sys.stderr)

USAGE = """\
%prog [Options...] CONF_PATH_OR_PATTERN_0 [CONF_PATH_OR_PATTERN_1 ..]

Examples:
  %prog --list  # -> Supported config types: configobj, ini, json, ...
  # Merge and/or convert input config to output config [file]
  %prog -I yaml -O yaml /etc/xyz/conf.d/a.conf
  %prog -I yaml '/etc/xyz/conf.d/*.conf' -o xyz.conf --otype json
  %prog '/etc/xyz/conf.d/*.json' -o xyz.yml \\
    --atype json -A '{"obsoletes": "syscnf", "conflicts": "syscnf-old"}'
  %prog '/etc/xyz/conf.d/*.json' -o xyz.yml \\
    -A obsoletes:syscnf;conflicts:syscnf-old
  %prog /etc/foo.json /etc/foo/conf.d/x.json /etc/foo/conf.d/y.json
  %prog '/etc/foo.d/*.json' -M noreplace
  # Get/set part of input config
  %prog '/etc/foo.d/*.json' --get a.b.c
  %prog '/etc/foo.d/*.json' --set a.b.c=1"""


def to_log_level(level):
    """
    :param level: Logging level in int = 0 .. 2

    >>> to_log_level(0) == logging.WARN
    True
    >>> to_log_level(5)  # doctest: +IGNORE_EXCEPTION_DETAIL, +ELLIPSIS
    Traceback (most recent call last):
        ...
    ValueError: wrong log level passed: 5
    >>>
    """
    if not (level >= 0 and level < 3):
        raise ValueError("wrong log level passed: " + str(level))

    return [logging.WARN, logging.INFO, logging.DEBUG][level]


def option_parser(defaults=None, usage=USAGE):
    """
    Make up an option and arguments parser.

    :param defaults: Default option values
    :param usage: Usage text
    """
    defaults = dict(loglevel=1, list=False, output=None, itype=None,
                    otype=None, atype=None, merge=A.MS_DICTS,
                    ignore_missing=False, template=False, env=False,
                    schema=None, validate=False, gen_schema=False)

    ctypes = A.list_types()
    ctypes_s = ", ".join(ctypes)
    type_help = "Select type of %s config files from " + \
        ctypes_s + " [Automatically detected by file ext]"

    mts = A.MERGE_STRATEGIES
    mts_s = ", ".join(mts)
    mt_help = "Select strategy to merge multiple configs from " + \
        mts_s + " [%(merge)s]" % defaults

    af_help = """Explicitly select type of argument to provide configs from %s.

If this option is not set, original parser is used: 'K:V' will become {K: V},
'K:V_0,V_1,..' will become {K: [V_0, V_1, ...]}, and 'K_0:V_0;K_1:V_1' will
become {K_0: V_0, K_1: V_1} (where the tyep of K is str, type of V is one of
Int, str, etc.""" % ctypes_s

    get_help = ("Specify key path to get part of config, for example, "
                "'--get a.b.c' to config {'a': {'b': {'c': 0, 'd': 1}}} "
                "gives 0 and '--get a.b' to the same config gives "
                "{'c': 0, 'd': 1}.")
    set_help = ("Specify key path to set (update) part of config, for "
                "example, '--set a.b.c=1' to a config {'a': {'b': {'c': 0, "
                "'d': 1}}} gives {'a': {'b': {'c': 1, 'd': 1}}}.")

    parser = optparse.OptionParser(usage, version="%%prog %s" %
                                   anyconfig.globals.VERSION)
    parser.set_defaults(**defaults)

    lpog = optparse.OptionGroup(parser, "List specific options")
    lpog.add_option("-L", "--list", help="List supported config types",
                    action="store_true")
    parser.add_option_group(lpog)

    spog = optparse.OptionGroup(parser, "Schema specific options")
    spog.add_option("", "--validate", action="store_true",
                    help="Only validate input files and do not output. "
                         "You must specify schema file with -S/--schema "
                         "option.")
    spog.add_option("", "--gen-schema", action="store_true",
                    help="Generate JSON schema for givne config file[s] "
                         "and output it instead of (merged) configuration.")
    parser.add_option_group(spog)

    gspog = optparse.OptionGroup(parser, "Get/set options")
    gspog.add_option("", "--get", help=get_help)
    gspog.add_option("", "--set", help=set_help)
    parser.add_option_group(gspog)

    parser.add_option("-o", "--output", help="Output file path")
    parser.add_option("-I", "--itype", choices=ctypes,
                      help=(type_help % "Input"))
    parser.add_option("-O", "--otype", choices=ctypes,
                      help=(type_help % "Output"))
    parser.add_option("-M", "--merge", choices=mts, help=mt_help)
    parser.add_option("-A", "--args", help="Argument configs to override")
    parser.add_option("", "--atype", choices=ctypes, help=af_help)

    parser.add_option("-x", "--ignore-missing", action="store_true",
                      help="Ignore missing input files")
    parser.add_option("-T", "--template", action="store_true",
                      help="Enable template config support")
    parser.add_option("-E", "--env", action="store_true",
                      help="Load configuration defaults from "
                           "environment values")
    parser.add_option("-S", "--schema", help="Specify Schema file[s] path")
    parser.add_option("-s", "--silent", action="store_const", dest="loglevel",
                      const=0, help="Silent or quiet mode")
    parser.add_option("-q", "--quiet", action="store_const", dest="loglevel",
                      const=0, help="Same as --silent option")
    parser.add_option("-v", "--verbose", action="store_const", dest="loglevel",
                      const=2, help="Verbose mode")

    return parser


def main(argv=None):
    """
    :param argv: Argument list to parse or None (sys.argv will be set).
    """
    if argv is None:
        argv = sys.argv

    parser = option_parser()
    (options, args) = parser.parse_args(argv[1:])

    A.set_loglevel(to_log_level(options.loglevel))

    if not args:
        if options.list:
            tlist = ", ".join(A.list_types()) + "\n"
            sys.stdout.write("Supported config types: " + tlist)
            sys.exit(0)
        else:
            parser.print_usage()
            sys.exit(1)

    if options.validate and options.schema is None:
        sys.stderr.write("--validate option requires --scheme option")
        sys.exit(1)

    cnf = A.container(os.environ.copy()) if options.env else A.container()
    diff = A.load(args, options.itype,
                  ignore_missing=options.ignore_missing,
                  merge=options.merge, ac_template=options.template,
                  ac_schema=options.schema)

    if diff is None:
        sys.stderr.write("Validation failed")
        sys.exit(1)

    cnf.update(diff)

    if options.args:
        diff = A.loads(options.args, options.atype,
                       ac_template=options.template, ac_context=cnf)
        cnf.update(diff, options.merge)

    if options.validate:
        A.LOGGER.info("Validation succeeds")
        sys.exit(0)

    if options.gen_schema:
        cnf = A.gen_schema(cnf)

    if options.get:
        (cnf, err) = A.get(cnf, options.get)
        if err:
            raise RuntimeError(err)

        # Output primitive types as it is.
        if not anyconfig.mergeabledict.is_dict_like(cnf):
            sys.stdout.write(str(cnf) + '\n')
            return

    if options.set:
        (key, val) = options.set.split('=')
        A.set_(cnf, key, anyconfig.parser.parse(val))

    if options.output:
        cparser = A.find_loader(options.output, options.otype)
        if cparser is None:
            raise RuntimeError("No suitable dumper was found for %s",
                               options.output)

        cparser.dump(cnf, options.output)
    else:
        if options.otype is None:
            if options.itype is None:
                psr = A.find_loader(args[0])
                if psr is not None:
                    options.otype = psr.type()  # Reuse detected input type
                else:
                    raise RuntimeError("Please specify input and/or output "
                                       "type with -I (--itype) or -O "
                                       "(--otype) option")
            else:
                options.otype = options.itype

        cparser = A.find_loader(None, options.otype)
        sys.stdout.write(cparser.dumps(cnf) + '\n')


if __name__ == '__main__':
    main(sys.argv)

# vim:sw=4:ts=4:et:
