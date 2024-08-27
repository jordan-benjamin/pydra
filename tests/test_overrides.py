import unittest
from dataclasses import dataclass

from pydra import apply_overrides, Config, Alias, DataclassWrapper, REQUIRED


class TestConfig(Config):
    def __init__(self):
        self.foo1 = 1
        self.foo2 = "two"

    def bar1(self):
        self.foo1 = 10

    def inc_foo1(self, increment, extra_decrement=0):
        self.foo1 += increment - extra_decrement


class TestOverrides(unittest.TestCase):
    def setUp(self):
        self.conf = TestConfig()

    def test_empty_args(self):
        args = []
        show = apply_overrides(self.conf, args)
        self.assertFalse(show)
        self.assertEqual(self.conf.foo1, 1)
        self.assertEqual(self.conf.foo2, "two")

    def test_basic(self):
        args = ["foo1=12", "foo2=hi"]
        show = apply_overrides(self.conf, args)
        self.assertFalse(show)
        self.assertEqual(self.conf.foo1, 12)
        self.assertEqual(self.conf.foo2, "hi")

    def test_lists(self):
        args = ["foo1=[T,2,a]", "foo2=[a,None,1.0]"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.foo1, [True, 2, "a"])
        self.assertEqual(self.conf.foo2, ["a", None, 1.0])

    def test_mixed(self):
        args = ["foo1=12", "foo2=None", "foo1=[1,2,3]"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.foo1, [1, 2, 3])
        self.assertEqual(self.conf.foo2, None)

    def test_show_flag(self):
        args = ["foo1=12", "--show", "foo2=three"]
        show = apply_overrides(self.conf, args)
        self.assertTrue(show)

    def test_method_call(self):
        args = [".bar1"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.foo1, 10)

    def test_method_call_with_args(self):
        args = [".inc_foo1(5)"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.foo1, 6)

    def test_method_kwargs(self):
        args = [".inc_foo1(increment=5)"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.foo1, 6)

    def test_method_args_kwargs(self):
        args = [".inc_foo1(5,extra_decrement=1)"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.foo1, 5)

    def test_field_doesnt_exist(self):
        args = ["foo3=3"]
        with self.assertRaises(AttributeError):
            apply_overrides(self.conf, args)

    def test_field_addition(self):
        args = ["+foo3=3"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.foo3, 3)


class NestedConfig(Config):
    def __init__(self):
        self.nested_value = "original"
        self.long_name = 15
        self.short_name = Alias("long_name")


class ComplexTestConfig(Config):
    def __init__(self):
        self.nested = NestedConfig()
        self.normal_dict = {"a": 1, "b": 2}

        self.long_name = 5
        self.short_name = Alias("long_name")

        self.alias_nest = Alias("nested")


class TestExpandedOverrides(unittest.TestCase):
    def setUp(self):
        self.conf = ComplexTestConfig()

    def test_normal_dict_assignment(self):
        args = ["normal_dict.a=3"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.normal_dict, {"a": 3, "b": 2})

    def test_local_alias_assignment(self):
        args = ["short_name=20"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.long_name, 20)

    def test_nested_local_alias_assignment(self):
        args = ["nested.short_name=25"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.nested.long_name, 25)

    def test_nested_alias_assignment(self):
        args = ["alias_nest.long_name=30"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.nested.long_name, 30)

    def test_mixed_alias_assignments(self):
        args = ["short_name=40", "nested.short_name=35"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.long_name, 40)
        self.assertEqual(self.conf.nested.long_name, 35)

    def test_alias_short_then_long(self):
        args = ["short_name=40", "long_name=2"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.long_name, 2)

    def test_alias_long_then_short(self):
        args = ["long_name=2", "short_name=40"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.long_name, 40)

    def test_double_alias(self):
        args = ["alias_nest.short_name=45"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.nested.long_name, 45)

    def test_alias_with_scope(self):
        args = ["--in", "nested", "short_name=45", "in--"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.nested.long_name, 45)


@dataclass
class MyDataclass:
    x: int
    y: str
    z: float = 1.0


class DC_Config(Config):
    def __init__(self):
        self.dc = DataclassWrapper(MyDataclass)

    def finalize(self):
        self.built_dc = self.dc.build()


class TestDataclassConfig(unittest.TestCase):
    def setUp(self):
        self.conf = DC_Config()

    def test_dataclass_assignment(self):
        args = ["dc.x=3", "dc.y=hi", "dc.z=2.0"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.built_dc, MyDataclass(3, "hi", 2.0))

    def test_dataclass_assignment_with_defaults(self):
        args = ["dc.x=3", "dc.y=hi"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.built_dc, MyDataclass(3, "hi"))

    def test_dataclass_missing_field(self):
        args = ["dc.x=3"]
        with self.assertRaises(ValueError):
            apply_overrides(self.conf, args)

    def test_assign_nonexistent_field(self):
        args = ["dc.w=3"]
        with self.assertRaises(AttributeError):
            apply_overrides(self.conf, args)


class NestedToSerialize(Config):
    def __init__(self):
        self.nested_foo = "nested_bar"


class ConfigToSerialize(Config):
    def __init__(self):
        self.foo = 1
        self.bar = "two"
        self.baz = 3.0
        self.qux = [1, 2, 3]
        self.qux_tuple = (1, 2, 3)
        self.quux = {"a": 1, "b": 2}
        self.nested = NestedToSerialize()


class TestConfigSerialization(unittest.TestCase):
    def setUp(self):
        self.conf = ConfigToSerialize()

    def test_serialization(self):
        args = [
            "foo=12",
            "bar=hi",
        ]
        apply_overrides(self.conf, args)
        serialized = self.conf.to_dict()
        expected = {
            "foo": 12,
            "bar": "hi",
            "baz": 3.0,
            "qux": [1, 2, 3],
            "qux_tuple": [1, 2, 3],
            "quux": {"a": 1, "b": 2},
            "nested": {"nested_foo": "nested_bar"},
        }
        self.assertEqual(serialized, expected)


class ConfigWithRequired(Config):
    def __init__(self):
        self.required = REQUIRED
        self.optional = 5
        self.final_val = None

    def finalize(self):
        self.final_val = self.required + 1


class TestRequiredConfig(unittest.TestCase):
    def setUp(self):
        self.conf = ConfigWithRequired()

    def test_required_missing(self):
        with self.assertRaises(ValueError):
            apply_overrides(self.conf, ["optional=10"])

    def test_required_present(self):
        apply_overrides(self.conf, ["required=10"])
        self.assertEqual(self.conf.required, 10)

    def test_finalize(self):
        apply_overrides(self.conf, ["required=10"])
        self.assertEqual(self.conf.final_val, 11)


if __name__ == "__main__":
    unittest.main()
