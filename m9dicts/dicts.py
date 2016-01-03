#
# Copyright (C) 2011 - 2015 Red Hat, Inc.
# Copyright (C) 2011 - 2016 Satoru SATOH <ssato redhat.com>
# License: MIT
#
# .. note:: suppress warning about import error of ordereddict only for py-2.6.
# pylint: disable=import-error
"""Some dict-like classes support merge operations.
"""
from __future__ import absolute_import

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict  # Python 2.6

import m9dicts.globals as MG
import m9dicts.utils


def _are_list_like(*objs):
    """
    >>> _are_list_like([], (), [x for x in range(10)], (x for x in range(4)))
    True
    >>> _are_list_like([], {})
    False
    >>> _are_list_like([], "aaa")
    False
    """
    return all(m9dicts.utils.is_list_like(obj) for obj in objs)


class UpdateWithReplaceDict(dict):
    """
    Replace value of self with other's if both have same keys on update.
    Otherwise, just keep the value of self.

    >>> od0 = OrderedDict((("a", 1), ("b", [1, 3]), ("c", "abc"), ("f", None)))
    >>> md0 = UpdateWithReplaceDict(od0)
    >>> md1 = UpdateWithReplaceDict(od0.items())
    >>> ref = md0.copy()
    >>> upd = UpdateWithReplaceDict(a=2, b=[0, 1], c=dict(d="d", e=1), d="d")
    >>> md0.update(upd)
    >>> md1.update(upd)
    >>> all(md0[k] == upd[k] for k in upd.keys())
    True
    >>> all(md0[k] == ref[k] for k in ref.keys() if k not in upd)
    True
    >>> all(md1[k] == upd[k] for k in upd.keys())
    True
    >>> all(md1[k] == ref[k] for k in ref.keys() if k not in upd)
    True
    >>> md2 = UpdateWithReplaceDict(1)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    TypeError: ...
    """
    def _update(self, other, key, *args):
        """
        :param other: a dict[-like] object or a list of (key, value) tuples
        :param key: object key
        :param args: [] or (value, ...)
        """
        self[key] = args[0] if args else other[key]

    def update(self, *others, **another):
        """
        :param others:
            a list of dict[-like] objects or a list of (key, value) tuples to
            update self
        :param another: optional keyword arguments to update self more

        .. seealso:: Document of dict.update
        """
        for other in others:
            if hasattr(other, "keys"):
                for key in other.keys():
                    self._update(other, key)
            else:
                for key, val in other:  # TypeError, etc. may be raised.
                    self._update(other, key, val)

        for key in another.keys():
            self._update(another, key)


class UpdateWoReplaceDict(UpdateWithReplaceDict):
    """
    Never update (replace) the value of self with other's, that is, only the
    values self does not have its key will be added on update.

    >>> od0 = OrderedDict((("a", 1), ("b", [1, 3]), ("c", "abc"),
    ...                    ("f", None)))
    >>> md0 = UpdateWoReplaceDict(od0)
    >>> ref = md0.copy()
    >>> upd = UpdateWoReplaceDict(a=2, b=[0, 1], c="xyz", d=None)
    >>> md0.update(upd)
    >>> all(md0[k] == upd[k] for k in upd.keys() if k not in ref)
    True
    >>> all(md0[k] == ref[k] for k in ref.keys())
    True
    """
    def _update(self, other, key, *args):
        """
        :param other: a dict[-like] object or a list of (key, value) tuples
        :param key: object key
        :param args: [] or (value, ...)
        """
        if key not in self:
            self[key] = args[0] if args else other[key]


class UpdateWithMergeDict(UpdateWithReplaceDict):
    """
    Merge the value of self with other's recursively. Behavior of merge will be
    vary depends on types of original and new values.

    - dict-like vs. dict-like -> merge recursively
    - list vs. list -> vary depends on `merge_lists`. see its description.
    - other objects vs. any -> vary depends on `keep`. see its description.

    class variables:

        - merge_lists: Merge not only dicts but also lists. For example,

            [1, 2, 3], [3, 4] ==> [1, 2, 3, 4]
            [1, 2, 2], [2, 4] ==> [1, 2, 2, 4]

        - keep: Keep original value if type of original value is not a dict nor
          list. It will be simply replaced with new value by default.

    >>> od0 = OrderedDict((("c", 2), ("d", 3)))
    >>> od1 = OrderedDict((("c", 4), ("d", 5), ("g", None)))
    >>> md0 = UpdateWithMergeDict((("a", 1),
    ...                            ("b", UpdateWithMergeDict(od0)),
    ...                            ("e", [1, 2, 2]), ("f", None)))
    >>> ref = md0.copy()
    >>> upd = UpdateWithMergeDict((("a", 2),
    ...                            ("b", UpdateWithMergeDict(od1)),
    ...                            ("e", [2, 3, 4])))
    >>> md0.update(upd)
    >>> all(md0[k] == upd[k] for k in ("a", "e"))  # vary depends on 'keep'.
    True
    >>> all(md0["b"][k] == ref["b"][k] for k in ref["b"].keys())
    True
    >>> all(md0[k] == ref[k] for k in ref.keys() if k not in upd)
    True
    """
    merge_lists = False
    keep = False

    def _update(self, other, key, *args):
        """
        :param other: a dict[-like] object or a list of (key, value) tuples
        :param key: object key
        :param args: [] or (value, ...)
        """
        val = args[0] if args else other[key]
        if key in self:
            val0 = self[key]  # Original value
            if m9dicts.utils.is_dict_like(val0):  # It needs recursive updates.
                self[key].update(val)
            elif self.merge_lists and _are_list_like(val, val0):
                self[key] += [x for x in val if x not in val0]
            elif not self.keep:
                self[key] = val  # Overwrite it.
        else:
            self[key] = val


class UpdateWithMergeListsDict(UpdateWithMergeDict):
    """
    Similar to UpdateWithMergeDict but merge lists by default.

    >>> md0 = UpdateWithMergeListsDict(aaa=[1, 2, 3])
    >>> upd = UpdateWithMergeListsDict(aaa=[4, 4, 5])
    >>> md0.update(upd)
    >>> md0["aaa"]
    [1, 2, 3, 4, 4, 5]
    """
    merge_lists = True


class UpdateWithReplaceOrderedDict(UpdateWithReplaceDict, OrderedDict):
    """
    Similar to UpdateWithReplaceDict but keep keys' order like OrderedDict.

    >>> od0 = OrderedDict((("a", 1), ("b", [1, 3]), ("c", "abc"), ("f", None)))
    >>> od1 = OrderedDict((("a", 2), ("b", [0, 1]),
    ...                    ("c", OrderedDict((("d", "d"), ("e", 1)))),
    ...                    ("d", "d")))
    >>> md0 = UpdateWithReplaceOrderedDict(od0)
    >>> md1 = UpdateWithReplaceOrderedDict(od0.items())
    >>> ref = md0.copy()
    >>> upd = UpdateWithReplaceOrderedDict(od1)
    >>> md0.update(upd)
    >>> md1.update(upd)
    >>> all(md0[k] == upd[k] for k in upd.keys())
    True
    >>> all(md0[k] == ref[k] for k in ref.keys() if k not in upd)
    True
    >>> all(md1[k] == upd[k] for k in upd.keys())
    True
    >>> all(md1[k] == ref[k] for k in ref.keys() if k not in upd)
    True
    >>> list(md0.keys())
    ['a', 'b', 'c', 'f', 'd']
    >>> list(md1.keys())
    ['a', 'b', 'c', 'f', 'd']
    """
    pass


class UpdateWoReplaceOrderedDict(UpdateWoReplaceDict, OrderedDict):
    """
    Similar to UpdateWoReplaceDict but keep keys' order like OrderedDict.

    >>> od0 = OrderedDict((("a", 1), ("b", [1, 3]), ("c", "abc"),
    ...                    ("f", None)))
    >>> md0 = UpdateWoReplaceOrderedDict(od0)
    >>> ref = md0.copy()
    >>> md1 = UpdateWoReplaceOrderedDict((("a", 2), ("b", [0, 1]),
    ...                                   ("c", "xyz"), ("d", None)))
    >>> md0.update(md1)
    >>> all(md0[k] == md1[k] for k in md1.keys() if k not in ref)
    True
    >>> all(md0[k] == ref[k] for k in ref.keys())
    True
    >>> list(md0.keys())
    ['a', 'b', 'c', 'f', 'd']
    """
    pass


class UpdateWithMergeOrderedDict(UpdateWithMergeDict, OrderedDict):
    """
    Similar to UpdateWithMergeDict but keep keys' order like OrderedDict.

    >>> od0 = OrderedDict((("c", 2), ("d", 3)))
    >>> od1 = OrderedDict((("c", 4), ("d", 5), ("g", None)))
    >>> md0 = UpdateWithMergeOrderedDict(
    ...          OrderedDict((("a", 1),
    ...                       ("b", UpdateWithMergeOrderedDict(od0)),
    ...                       ("e", [1, 2, 2]), ("f", None))))
    >>> ref = md0.copy()
    >>> upd = dict(a=2, b=UpdateWithMergeOrderedDict(od1), e=[2, 3, 4])
    >>> md0.update(upd)
    >>> all(md0[k] == upd[k] for k in ("a", "e"))  # vary depends on 'keep'.
    True
    >>> all(md0[k] == ref[k] for k in ref.keys() if k not in upd)
    True
    >>> all(md0["b"][k] == ref["b"][k] for k in ref["b"].keys())
    True
    >>> list(md0.keys())
    ['a', 'b', 'e', 'f']
    >>> list(md0["b"].keys())
    ['c', 'd', 'g']
    """
    pass


class UpdateWithMergeListsOrderedDict(UpdateWithMergeListsDict, OrderedDict):
    """
    Similar to UpdateWithMergeListsDict but keep keys' order like OrderedDict.

    >>> md0 = UpdateWithMergeListsOrderedDict((("aaa", [1, 2, 3]), ('b', 0)))
    >>> upd = UpdateWithMergeListsOrderedDict((("aaa", [4, 4, 5]), ))
    >>> md0.update(upd)
    >>> md0["aaa"]
    [1, 2, 3, 4, 4, 5]
    >>> list(md0.keys())
    ['aaa', 'b']
    """
    pass


# Mapppings: (merge_strategy, ordered?) : m9dict class
_MDICTS_MAP = {(MG.MS_REPLACE, True): UpdateWithReplaceOrderedDict,
               (MG.MS_REPLACE, False): UpdateWithReplaceDict,
               (MG.MS_NO_REPLACE, True): UpdateWoReplaceOrderedDict,
               (MG.MS_NO_REPLACE, False): UpdateWoReplaceDict,
               (MG.MS_DICTS, True): UpdateWithMergeOrderedDict,
               (MG.MS_DICTS, False): UpdateWithMergeDict,
               (MG.MS_DICTS_AND_LISTS, True): UpdateWithMergeListsOrderedDict,
               (MG.MS_DICTS_AND_LISTS, False): UpdateWithMergeListsDict}


def get_mdict_class(merge=MG.MS_DICTS, ordered=False):
    """
    Select dict-like class based on merge strategy and orderness of keys.

    :param merge: Specify strategy from MERGE_STRATEGIES of how to merge dicts.
    :param ordered:
        The class keeps the order of insertion keys such as
        UpdateWoReplaceOrderedDict will be chosen if True.

    :return: The dict class object
    """
    return _MDICTS_MAP.get((merge, ordered), UpdateWithMergeDict)

# vim:sw=4:ts=4:et:
