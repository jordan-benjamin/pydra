import unittest
from pathlib import Path
from typing import Optional

import pydra


class DoubleInt:
    def __init__(self, value: int):
        assert isinstance(value, int)
        self.value = value * 2


class ConfigWithAnnotations(pydra.Config):
    a: int = 4
    b: DoubleInt
    c: float = 6.0

    def __init__(self):
        super().__init__()
        self.d = "hi"


class ConfigWithOptional(pydra.Config):
    opt1: Optional[Path]


class DerivedConfigWithOptional(ConfigWithOptional):
    opt2: Path | None = None


class ConfigWithAnnotationsAndInit(pydra.Config):
    a: int = 4
    b: int = 1

    def __init__(self):
        super().__init__()
        self.a = 5


class TestAnnotations(unittest.TestCase):
    def test_annotations(self):
        config = ConfigWithAnnotations()

        pydra.apply_overrides(config, ["a=5.2", "b=11", "c=7.0", "d=bye"])

        self.assertEqual(config.a, 5)
        self.assertIsInstance(config.b, DoubleInt)
        self.assertEqual(config.b.value, 22)
        self.assertEqual(config.c, 7.0)
        self.assertEqual(config.d, "bye")

    def test_annotations_with_missing(self):
        config = ConfigWithAnnotations()

        with self.assertRaises(ValueError):
            pydra.apply_overrides(config, ["a=5.2", "c=7.0"])

    def test_optional_annotations(self):
        config = DerivedConfigWithOptional()
        pydra.apply_overrides(config, ["opt1=hi", "opt2=bye"])
        self.assertEqual(config.opt1, Path("hi"))
        self.assertEqual(config.opt2, Path("bye"))

        pydra.apply_overrides(config, ["opt1=foo", "opt2=None"])
        self.assertEqual(config.opt1, Path("foo"))
        self.assertIsNone(config.opt2)

    def test_annotations_and_init(self):
        config = ConfigWithAnnotationsAndInit()
        pydra.apply_overrides(config, ["b=2"])
        self.assertEqual(config.a, 5)
        self.assertEqual(config.b, 2)
