import unittest
import pydra
from typing import Optional
from pathlib import Path


class DoubleInt:
    def __init__(self, value: int):
        assert isinstance(value, int)
        self.value = value * 2


class ConfigWithAnnotations(pydra.Config):
    a: int = 4
    b: DoubleInt
    c: float = 6.0

    def __init__(self):
        self.d = "hi"


class ConfigWithOptional(pydra.Config):
    opt1: Optional[Path]
    opt2: Path | None = Path("foo")


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
        config = ConfigWithOptional()
        pydra.apply_overrides(config, ["opt1=hi", "opt2=bye"])
        self.assertEqual(config.opt1, Path("hi"))
        self.assertEqual(config.opt2, Path("bye"))

        pydra.apply_overrides(config, ["opt1=None", "opt2=None"])
        self.assertIsNone(config.opt1)
        self.assertIsNone(config.opt2)
