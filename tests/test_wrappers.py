import unittest
from pydra import DataclassWrapper, PydanticWrapper, Config, apply_overrides
from pydantic import BaseModel, Field
from dataclasses import dataclass, field


@dataclass
class MyDataclass:
    a: int
    b: list[int] = field(default_factory=list)
    c: float = 4.0


class MyPydantic(BaseModel):
    a: int
    b: list[int] = Field(default_factory=list)
    c: float = 4.0


class MyConfig(Config):
    def __init__(self):
        self.wrapped_dataclass = DataclassWrapper(MyDataclass)
        self.wrapped_pydantic = PydanticWrapper(MyPydantic)


class TestWrappers(unittest.TestCase):
    def setUp(self):
        self.conf = MyConfig()

    def test_full_override_wrappers(self):
        apply_overrides(
            self.conf,
            [
                "wrapped_dataclass.a=1",
                "wrapped_dataclass.b=[1,2]",
                "wrapped_dataclass.c=3",
                "wrapped_pydantic.a=4",
                "wrapped_pydantic.b=[5,6,7]",
                "wrapped_pydantic.c=8",
            ],
        )

        built_dataclass = self.conf.wrapped_dataclass.build()

        self.assertEqual(built_dataclass.a, 1)
        self.assertEqual(built_dataclass.b, [1, 2])
        self.assertEqual(built_dataclass.c, 3)

        built_pydantic = self.conf.wrapped_pydantic.build()

        self.assertEqual(built_pydantic.a, 4)
        self.assertEqual(built_pydantic.b, [5, 6, 7])
        self.assertEqual(built_pydantic.c, 8)

    def test_default_values_wrappers(self):
        apply_overrides(
            self.conf,
            [
                "wrapped_dataclass.a=1",
                "wrapped_dataclass.b=[1,2]",
                "wrapped_pydantic.a=4",
                "wrapped_pydantic.b=[5,6,7]",
            ],
        )

        built_dataclass = self.conf.wrapped_dataclass.build()
        self.assertEqual(built_dataclass.a, 1)
        self.assertEqual(built_dataclass.b, [1, 2])
        self.assertEqual(built_dataclass.c, 4.0)

        built_pydantic = self.conf.wrapped_pydantic.build()
        self.assertEqual(built_pydantic.a, 4)
        self.assertEqual(built_pydantic.b, [5, 6, 7])
        self.assertEqual(built_pydantic.c, 4.0)

    def test_default_factory_wrappers(self):
        apply_overrides(
            self.conf,
            [
                "wrapped_dataclass.a=1",
                "wrapped_dataclass.c=4",
                "wrapped_pydantic.a=4",
                "wrapped_pydantic.c=8",
            ],
        )

        built_dataclass = self.conf.wrapped_dataclass.build()
        self.assertEqual(built_dataclass.a, 1)
        self.assertEqual(built_dataclass.b, [])
        self.assertEqual(built_dataclass.c, 4.0)

        built_pydantic = self.conf.wrapped_pydantic.build()
        self.assertEqual(built_pydantic.a, 4)
        self.assertEqual(built_pydantic.b, [])
        self.assertEqual(built_pydantic.c, 8.0)

    def test_missing_field_wrappers(self):
        with self.assertRaises(ValueError):
            self.conf.wrapped_dataclass.build()

        with self.assertRaises(ValueError):
            self.conf.wrapped_pydantic.build()


if __name__ == "__main__":
    unittest.main()
