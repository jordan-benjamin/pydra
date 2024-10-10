import pickle
import unittest
from copy import deepcopy
from dataclasses import dataclass

import pydra


@dataclass
class MyClass:
    x: int
    y: str = "hello"


class TestConfig(pydra.Config):
    def __init__(self):
        self.foo1 = 1
        self.foo2 = "two"
        self.inner = pydra.DataclassWrapper(MyClass)


class TestPickle(unittest.TestCase):
    def test_pickle(self):
        conf = TestConfig()

        pydra.apply_overrides(
            conf,
            [
                "foo1=10",
                "foo2=astring",
                "inner.x=11",
                "inner.y=bstring",
            ],
        )

        pkl = pickle.dumps(conf)
        _ = pickle.loads(pkl)

        self.assertEqual(conf.foo1, 10)
        self.assertEqual(conf.foo2, "astring")

        inner = conf.inner.build()
        self.assertEqual(inner.x, 11)
        self.assertEqual(inner.y, "bstring")

    def test_deepcopy(self):
        conf = TestConfig()

        pydra.apply_overrides(
            conf,
            [
                "foo1=10",
                "foo2=astring",
                "inner.x=11",
                "inner.y=bstring",
            ],
        )

        conf_copy = deepcopy(conf)

        pydra.apply_overrides(
            conf_copy,
            [
                "foo1=100",
                "inner.x=111",
            ],
        )

        self.assertEqual(conf.foo1, 10)
        self.assertEqual(conf.foo2, "astring")

        self.assertEqual(conf_copy.foo1, 100)
        self.assertEqual(conf_copy.foo2, "astring")

        inner = conf.inner.build()
        self.assertEqual(inner.x, 11)
        self.assertEqual(inner.y, "bstring")

        inner_copy = conf_copy.inner.build()
        self.assertEqual(inner_copy.x, 111)
        self.assertEqual(inner_copy.y, "bstring")
