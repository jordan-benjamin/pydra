import unittest

from pydra import Config, apply_overrides


class NestedStructConfig(Config):
    def __init__(self):
        self.simple_list = []
        self.nested_list = []
        self.dict_value = {}
        self.mixed_structure = None
        self.tuple_value = None


class TestEndToEndNestedStructures(unittest.TestCase):
    def setUp(self):
        self.conf = NestedStructConfig()

    def test_simple_nested_list_override(self):
        args = ["nested_list=[[1,2],[3,4]]"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.nested_list, [[1, 2], [3, 4]])

    def test_deeply_nested_list_override(self):
        args = ["nested_list=[[[1,2],3],[4,[5,6]]]"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.nested_list, [[[1, 2], 3], [4, [5, 6]]])

    def test_dict_override(self):
        args = ['dict_value={"a": 1, "b": 2, "c": [1,2,3]}']
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.dict_value, {"a": 1, "b": 2, "c": [1, 2, 3]})

    def test_nested_dict_override(self):
        args = ['dict_value={"outer": {"inner": [1,2,3], "flag": True}}']
        apply_overrides(self.conf, args)
        self.assertEqual(
            self.conf.dict_value, {"outer": {"inner": [1, 2, 3], "flag": True}}
        )

    def test_mixed_structure_override(self):
        args = [
            'mixed_structure=[{"name": "item1", "values": [1,2,3]}, {"name": "item2", "values": [4,5,6]}]'
        ]
        apply_overrides(self.conf, args)
        self.assertEqual(
            self.conf.mixed_structure,
            [
                {"name": "item1", "values": [1, 2, 3]},
                {"name": "item2", "values": [4, 5, 6]},
            ],
        )

    def test_tuple_override(self):
        args = ["tuple_value=(1,2,3)"]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.tuple_value, (1, 2, 3))

    def test_multiple_nested_overrides(self):
        args = [
            "simple_list=[1,2,3]",
            "nested_list=[[1,2],[3,4]]",
            'dict_value={"a": [1,2], "b": {"nested": True}}',
            "tuple_value=((1,2),(3,4))",
        ]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.simple_list, [1, 2, 3])
        self.assertEqual(self.conf.nested_list, [[1, 2], [3, 4]])
        self.assertEqual(self.conf.dict_value, {"a": [1, 2], "b": {"nested": True}})
        self.assertEqual(self.conf.tuple_value, ((1, 2), (3, 4)))

    def test_expression_in_parentheses(self):
        args = [
            "simple_list=([1,2] + [3,4])",
            'mixed_structure=({"a": 1, "b": 2}.items())',
        ]
        apply_overrides(self.conf, args)
        self.assertEqual(self.conf.simple_list, [1, 2, 3, 4])
        self.assertEqual(list(self.conf.mixed_structure), [("a", 1), ("b", 2)])


if __name__ == "__main__":
    unittest.main()
