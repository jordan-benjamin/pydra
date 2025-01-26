import unittest
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
        self.d = "hi"


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
