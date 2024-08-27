import unittest
from dataclasses import dataclass
import pickle

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
