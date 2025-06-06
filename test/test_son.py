# Copyright 2009-present MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the son module."""
from __future__ import annotations

import copy
import pickle
import re
import sys

sys.path[0:0] = [""]

from collections import OrderedDict
from test import unittest

from bson.son import SON


class TestSON(unittest.TestCase):
    def test_ordered_dict(self):
        a1 = SON()
        a1["hello"] = "world"
        a1["mike"] = "awesome"
        a1["hello_"] = "mike"
        self.assertEqual(
            list(a1.items()), [("hello", "world"), ("mike", "awesome"), ("hello_", "mike")]
        )

        b2 = SON({"hello": "world"})
        self.assertEqual(b2["hello"], "world")
        self.assertRaises(KeyError, lambda: b2["goodbye"])

    def test_equality(self):
        a1 = SON({"hello": "world"})
        b2 = SON((("hello", "world"), ("mike", "awesome"), ("hello_", "mike")))

        self.assertEqual(a1, SON({"hello": "world"}))
        self.assertEqual(b2, SON((("hello", "world"), ("mike", "awesome"), ("hello_", "mike"))))
        self.assertEqual(b2, {"hello_": "mike", "mike": "awesome", "hello": "world"})

        self.assertNotEqual(a1, b2)
        self.assertNotEqual(b2, SON((("hello_", "mike"), ("mike", "awesome"), ("hello", "world"))))

        # Explicitly test inequality
        self.assertFalse(a1 != SON({"hello": "world"}))
        self.assertFalse(b2 != SON((("hello", "world"), ("mike", "awesome"), ("hello_", "mike"))))
        self.assertFalse(b2 != {"hello_": "mike", "mike": "awesome", "hello": "world"})

        # Embedded SON.
        d4 = SON([("blah", {"foo": SON()})])
        self.assertEqual(d4, {"blah": {"foo": {}}})
        self.assertEqual(d4, {"blah": {"foo": SON()}})
        self.assertNotEqual(d4, {"blah": {"foo": []}})

        # Original data unaffected.
        self.assertEqual(SON, d4["blah"]["foo"].__class__)

    def test_to_dict(self):
        a1 = SON()
        b2 = SON([("blah", SON())])
        c3 = SON([("blah", [SON()])])
        d4 = SON([("blah", {"foo": SON()})])
        self.assertEqual({}, a1.to_dict())
        self.assertEqual({"blah": {}}, b2.to_dict())
        self.assertEqual({"blah": [{}]}, c3.to_dict())
        self.assertEqual({"blah": {"foo": {}}}, d4.to_dict())
        self.assertEqual(dict, a1.to_dict().__class__)
        self.assertEqual(dict, b2.to_dict()["blah"].__class__)
        self.assertEqual(dict, c3.to_dict()["blah"][0].__class__)
        self.assertEqual(dict, d4.to_dict()["blah"]["foo"].__class__)

        # Original data unaffected.
        self.assertEqual(SON, d4["blah"]["foo"].__class__)

    def test_pickle(self):
        simple_son = SON([])
        complex_son = SON([("son", simple_son), ("list", [simple_son, simple_son])])

        for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
            pickled = pickle.loads(pickle.dumps(complex_son, protocol=protocol))
            self.assertEqual(pickled["son"], pickled["list"][0])
            self.assertEqual(pickled["son"], pickled["list"][1])

    def test_pickle_backwards_compatability(self):
        # This string was generated by pickling a SON object in pymongo
        # version 2.1.1
        pickled_with_2_1_1 = (
            b"ccopy_reg\n_reconstructor\np0\n(cbson.son\nSON\np1\n"
            b"c__builtin__\ndict\np2\n(dp3\ntp4\nRp5\n(dp6\n"
            b"S'_SON__keys'\np7\n(lp8\nsb."
        )
        son_2_1_1 = pickle.loads(pickled_with_2_1_1)
        self.assertEqual(son_2_1_1, SON([]))

    def test_copying(self):
        simple_son = SON([])
        complex_son = SON([("son", simple_son), ("list", [simple_son, simple_son])])
        regex_son = SON([("x", re.compile("^hello.*"))])
        reflexive_son = SON([("son", simple_son)])
        reflexive_son["reflexive"] = reflexive_son

        simple_son1 = copy.copy(simple_son)
        self.assertEqual(simple_son, simple_son1)

        complex_son1 = copy.copy(complex_son)
        self.assertEqual(complex_son, complex_son1)

        regex_son1 = copy.copy(regex_son)
        self.assertEqual(regex_son, regex_son1)

        reflexive_son1 = copy.copy(reflexive_son)
        self.assertEqual(reflexive_son, reflexive_son1)

        # Test deepcopying
        simple_son1 = copy.deepcopy(simple_son)
        self.assertEqual(simple_son, simple_son1)

        regex_son1 = copy.deepcopy(regex_son)
        self.assertEqual(regex_son, regex_son1)

        complex_son1 = copy.deepcopy(complex_son)
        self.assertEqual(complex_son, complex_son1)

        reflexive_son1 = copy.deepcopy(reflexive_son)
        self.assertEqual(list(reflexive_son), list(reflexive_son1))
        self.assertEqual(id(reflexive_son1), id(reflexive_son1["reflexive"]))

    def test_iteration(self):
        """Test __iter__"""
        # test success case
        test_son = SON([(1, 100), (2, 200), (3, 300)])
        for ele in test_son:
            self.assertEqual(ele * 100, test_son[ele])

    def test_contains_has(self):
        """has_key and __contains__"""
        test_son = SON([(1, 100), (2, 200), (3, 300)])
        self.assertIn(1, test_son)
        self.assertIn(2, test_son, "in failed")
        self.assertNotIn(22, test_son, "in succeeded when it shouldn't")
        self.assertTrue(test_son.has_key(2), "has_key failed")
        self.assertFalse(test_son.has_key(22), "has_key succeeded when it shouldn't")

    def test_clears(self):
        """Test clear()"""
        test_son = SON([(1, 100), (2, 200), (3, 300)])
        test_son.clear()
        self.assertNotIn(1, test_son)
        self.assertEqual(0, len(test_son))
        self.assertEqual(0, len(test_son.keys()))
        self.assertEqual({}, test_son.to_dict())

    def test_len(self):
        """Test len"""
        test_son = SON()
        self.assertEqual(0, len(test_son))
        test_son = SON([(1, 100), (2, 200), (3, 300)])
        self.assertEqual(3, len(test_son))
        test_son.popitem()
        self.assertEqual(2, len(test_son))

    def test_keys(self):
        # Test to make sure that set operations do not throw an error
        d = SON().keys()
        for i in [OrderedDict, dict]:
            try:
                d - i().keys()
            except TypeError:
                self.fail(
                    "SON().keys() is not returning an object compatible "
                    "with %s objects" % (str(i))
                )
        # Test to verify correctness
        d = SON({"k": "v"}).keys()
        for i in [OrderedDict, dict]:
            self.assertEqual(d | i({"k1": 0}).keys(), {"k", "k1"})
        for i in [OrderedDict, dict]:
            self.assertEqual(d - i({"k": 0}).keys(), set())


if __name__ == "__main__":
    unittest.main()
