import unittest

from pydra.parser import (
    Assignment,
    KeyValuePair,
    MethodCall,
    ParseResult,
    parse,
)


class TestParseFunction(unittest.TestCase):
    def test_empty_args(self):
        args = []
        result = parse(args)
        expected = ParseResult(show=False, commands=[])
        self.assertEqual(result, expected)

    def test_show_flag(self):
        args = ["--show"]
        result = parse(args)
        expected = ParseResult(show=True, commands=[])
        self.assertEqual(result, expected)

    def test_single_key_value_assignment(self):
        args = ["key=value"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value="value"))],
        )
        self.assertEqual(result, expected)

    def test_misparse_key(self):
        args = ["key"]
        with self.assertRaises(ValueError):
            parse(args)

    def test_empty_value(self):
        args = ["key="]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value=""))],
        )
        self.assertEqual(result, expected)

    def test_string_literal(self):
        args = ['key="4"']
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value="4"))],
        )
        self.assertEqual(result, expected)

    def test_integer_value_assignment(self):
        args = ["key=123"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value=123))],
        )
        self.assertEqual(result, expected)

    def test_float_value_assignment(self):
        args = ["key=123.456"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value=123.456))],
        )
        self.assertEqual(result, expected)

    def test_boolean_true_value_assignment(self):
        args = ["key=True"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value=True))],
        )
        self.assertEqual(result, expected)

    def test_shorthand_boolean_false_value_assignment(self):
        args = ["key=F"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value=False))],
        )
        self.assertEqual(result, expected)

    def test_string_literal_assignment(self):
        args = ['key="0"']
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value="0"))],
        )
        self.assertEqual(result, expected)

    def test_list_assignment(self):
        args = ['key=[1,"3",None]']
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[
                Assignment(kv_pair=KeyValuePair(key="key", value=[1, "3", None]))
            ],
        )
        self.assertEqual(result, expected)

    def test_empty_list_assignment(self):
        args = ["key=[]"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value=[]))],
        )
        self.assertEqual(result, expected)

    def test_python_expression_assignment(self):
        args = ["key=(1+2)"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value=3))],
        )
        self.assertEqual(result, expected)

    def test_null_value_assignment(self):
        args = ["key=None"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value=None))],
        )
        self.assertEqual(result, expected)

    def test_equals_in_value(self):
        args = ["key=a=b"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="key", value="a=b"))],
        )
        self.assertEqual(result, expected)

    def test_method_call_no_args(self):
        args = [".method"]
        result = parse(args)
        expected = ParseResult(show=False, commands=[MethodCall(method_name="method")])
        self.assertEqual(result, expected)

    def test_method_call_with_args(self):
        args = [".method(pos1,key1=val1,key2=123)"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[
                MethodCall(
                    method_name="method",
                    args=["pos1"],
                    kwargs={"key1": "val1", "key2": 123},
                )
            ],
        )
        self.assertEqual(result, expected)

    def test_scoped_key_value_assignment(self):
        args = ["--in", "scope", "key=value", "in--"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[Assignment(kv_pair=KeyValuePair(key="scope.key", value="value"))],
        )
        self.assertEqual(result, expected)

    def test_dashed_list_assignment(self):
        args = ["--list", "key", "value1", "value2", "list--"]
        result = parse(args)
        expected = ParseResult(
            show=False,
            commands=[
                Assignment(kv_pair=KeyValuePair(key="key", value=["value1", "value2"]))
            ],
        )
        self.assertEqual(result, expected)

    def test_end_to_end(self):
        args = [
            ".foo",
            "--show",
            "--in",
            "scope1",
            "key1=value1",
            "--in",
            "scope2",
            "key2=123",
            "key3=45.67",
            "key4=True",
            "key5=None",
            "key6=[1,2,3]",
            "key7=(4+5)",
            "in--",
            "key8=False",
            "in--",
            "--list",
            "key9",
            "val1",
            "val2",
            "list--",
            ".method(arg1=val1,arg2=789)",
        ]

        result = parse(args)
        expected = ParseResult(
            show=True,
            commands=[
                MethodCall(method_name="foo"),
                Assignment(kv_pair=KeyValuePair(key="scope1.key1", value="value1")),
                Assignment(kv_pair=KeyValuePair(key="scope1.scope2.key2", value=123)),
                Assignment(kv_pair=KeyValuePair(key="scope1.scope2.key3", value=45.67)),
                Assignment(kv_pair=KeyValuePair(key="scope1.scope2.key4", value=True)),
                Assignment(kv_pair=KeyValuePair(key="scope1.scope2.key5", value=None)),
                Assignment(
                    kv_pair=KeyValuePair(key="scope1.scope2.key6", value=[1, 2, 3])
                ),
                Assignment(kv_pair=KeyValuePair(key="scope1.scope2.key7", value=9)),
                Assignment(kv_pair=KeyValuePair(key="scope1.key8", value=False)),
                Assignment(kv_pair=KeyValuePair(key="key9", value=["val1", "val2"])),
                MethodCall(method_name="method", kwargs={"arg1": "val1", "arg2": 789}),
            ],
        )
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
