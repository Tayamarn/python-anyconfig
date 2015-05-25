#
# Copyright (C) 2011 - 2015 Satoru SATOH <ssato @ redhat.com>
# License: MIT
#
# pylint: disable=R0921
"""XML files parser backend, should be available always.
"""
import logging

import anyconfig.backend.base as Base
import anyconfig.compat

try:
    # First, try lxml which is compatible with elementtree and looks faster a
    # lot. See also: http://getpython3.com/diveintopython3/xml.html
    from lxml2 import etree
except ImportError:
    try:
        import xml.etree.ElementTree as etree
    except ImportError:
        import elementtree.ElementTree as etree


def etree_getroot_fromstring(s):
    """
    :param s: A XML string
    :return: etree object gotten by parsing ``s``
    """
    return etree.ElementTree(etree.fromstring(s)).getroot()


def etree_getroot_fromsrc(src):
    """
    :param src: A file name/path or a file[-like] object or a URL
    :return: etree object gotten by parsing ``s``
    """
    return etree.parse(src).getroot()


def etree_to_container(root, container):
    """
    Convert XML ElementTree to a collection of container objects.

    :param root: etree root object or None
    :param container: A nested dict like objects
    """
    tree = container()
    if root is None:
        return tree

    tree[root.tag] = container()

    if root.attrib:
        tree[root.tag]["attrs"] = \
            container(anyconfig.compat.iteritems(root.attrib))

    if root.text and root.text.strip():
        tree[root.tag]["text"] = root.text.strip()

    if len(root):  # It has children.
        # FIXME: Configuration item cannot have both attributes and
        # values (list) at the same time in current implementation:
        tree[root.tag]["children"] = [etree_to_container(c, container) for c
                                      in root]

    return tree


class XmlConfigParser(Base.ConfigParser):
    """
    Parser for XML files.

    - Backend: one of the followings

      - lxml2.etree if available
      - xml.etree.ElementTree in standard lib if python >= 2.5
      - elementtree.ElementTree (otherwise)

    - Limitations:

      - 'attrs', 'text' and 'children' are used as special keyword to keep XML
        structure of config data so that these are not allowed to used in
        config files.

      - Some data or structures of original XML file may be lost if make it
        backed to XML file;
        XML file - (anyconfig.load) -> config - (anyconfig.dump) -> XML file

    - Special Options: None supported
    """
    _type = "xml"
    _extensions = ["xml"]

    @classmethod
    def loads(cls, config_content, **kwargs):
        """
        :param config_content:  Config file content
        :param kwargs: optional keyword parameters to be sanitized :: dict

        :return: cls.container() object holding config parameters
        """
        root = etree_getroot_fromstring(config_content)
        return etree_to_container(root, cls.container())

    @classmethod
    def load(cls, config_path, **kwargs):
        """
        :param config_path:  Config file path
        :param kwargs: optional keyword parameters to be sanitized :: dict

        :return: cls.container() object holding config parameters
        """
        root = etree_getroot_fromsrc(config_path)
        return etree_to_container(root, cls.container())

    @classmethod
    def dumps_impl(cls, data, **kwargs):
        """
        :param data: Data to dump :: dict
        :param kwargs: backend-specific optional keyword parameters :: dict

        :return: string represents the configuration
        """
        raise NotImplementedError("XML dumper not implemented yet!")

# vim:sw=4:ts=4:et:
