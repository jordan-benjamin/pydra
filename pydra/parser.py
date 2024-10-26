from dataclasses import dataclass, field
from typing import Union, Any


@dataclass
class KeyValuePair:
    key: str
    value: Any


@dataclass
class MethodCall:
    method_name: str
    args: list = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class Assignment:
    kv_pair: KeyValuePair
    assert_exists: bool


@dataclass
class ParseResult:
    show: bool
    commands: list[Union[Assignment, MethodCall]]


# builtin functions don't handle whitespace
def isfloat(value: str):
    try:
        float(value)
        return True
    except ValueError:
        return False


def isint(value: str):
    try:
        int(value)
        return True
    except ValueError:
        return False


def parse_value(value: str):
    # convert value to int or float if possible
    if isint(value):
        return int(value)
    elif isfloat(value):
        return float(value)
    elif value in ["None"]:
        return None
    elif value in ["T", "True"]:
        return True
    elif value in ["F", "False"]:
        return False
    elif value.startswith("[") and value.endswith("]"):
        return [parse_value(x) for x in value[1:-1].split(",")]
    elif value.startswith("(") and value.endswith(")"):
        sliced = value[1:-1]
        return eval(sliced)
    else:
        return value


def scope_key(scope: list[str], key: str):
    if len(scope) == 0:
        return key
    return ".".join(scope + [key])


def parse_kv_pair(kv_pair_arg: str, scope: list[str]) -> KeyValuePair:
    """Parse a string of the form 'key=value'"""
    try:
        key, value = kv_pair_arg.split("=")
    except:
        raise ValueError(f"Couldn't parse {kv_pair_arg}")
    return KeyValuePair(scope_key(scope=scope, key=key), value=parse_value(value))


def parse(args) -> ParseResult:
    current_scope = []
    show = False
    index = 0

    commands = []

    while index < len(args):
        arg = args[index]
        if arg == "--show":
            show = True
        elif arg == "--list":
            assert args[index + 1] != "list--"

            key = args[index + 1]
            index += 2

            list_args = []
            while args[index] != "list--":
                list_args.append(parse_value(args[index]))
                index += 1

            commands.append(
                Assignment(
                    kv_pair=KeyValuePair(key=key, value=list_args), assert_exists=True
                )
            )

        elif arg == "--in":
            current_scope.append(args[index + 1])
            index += 1
        elif arg == "in--":
            current_scope.pop()
        elif arg.startswith("."):
            if "(" not in arg:
                commands.append(MethodCall(method_name=arg[1:]))
            else:
                pos_left_paren = arg.index("(")
                pos_right_paren = arg.index(")")
                method_name = arg[1:pos_left_paren]
                method_contents_string = arg[pos_left_paren + 1 : pos_right_paren]
                method_contents = method_contents_string.split(",")

                method_args = []
                method_kwargs = {}

                for cont in method_contents:
                    if "=" in cont:
                        kv_pair_parsed = parse_kv_pair(cont, scope=[])
                        method_kwargs[kv_pair_parsed.key] = kv_pair_parsed.value
                    else:
                        if len(method_kwargs) > 0:
                            raise ValueError(
                                f"Positional argument {cont} after keyword arguments (for method {method_name}, args {method_contents_string})"
                            )
                        method_args.append(parse_value(cont))

                commands.append(
                    MethodCall(
                        method_name=method_name, args=method_args, kwargs=method_kwargs
                    )
                )

        else:
            assert_exists = True
            if arg.startswith("+"):
                assert_exists = False
                arg = arg[1:]
            commands.append(
                Assignment(
                    kv_pair=parse_kv_pair(arg, current_scope),
                    assert_exists=assert_exists,
                )
            )

        index += 1
    return ParseResult(show=show, commands=commands)
