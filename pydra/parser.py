import ast
from dataclasses import dataclass, field
from typing import Any, Union


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


@dataclass
class ParseResult:
    show: bool
    commands: list[Union[Assignment, MethodCall]]


def is_surrounded_by(value: str, left: str, right: str):
    return value.startswith(left) and value.endswith(right)


def parse_value(value: str):
    # Handle boolean shortcuts
    if value == "T":
        return True
    elif value == "F":
        return False

    # Handle expressions in parentheses using eval.
    elif is_surrounded_by(value, "(", ")"):
        return eval(value[1:-1])
    else:
        try:
            return ast.literal_eval(value)
        except Exception:
            # Special case: when passed something like foo=[1,2,a], we probably
            # want this to crash, since the user probably wants a parse result
            # of [1,2,'a'] (which you can get with foo="[1,2,'a']" syntax),
            # not a parsed string literal "[1,2,a]". The same goes for dicts and sets.
            if is_surrounded_by(value, "[", "]") or is_surrounded_by(value, "{", "}"):
                raise ValueError(f"Couldn't parse collection: '{value}'")

            # default to just returning the string
            return value


def scope_key(scope: list[str], key: str):
    if len(scope) == 0:
        return key
    return ".".join(scope + [key])


def parse_kv_pair(kv_pair_arg: str, scope: list[str]) -> KeyValuePair:
    """Parse a string of the form 'key=value'"""
    try:
        equals_pos = kv_pair_arg.index("=")
        key = kv_pair_arg[:equals_pos]
        value = kv_pair_arg[equals_pos + 1 :]
    except ValueError:
        raise ValueError(f"Couldn't parse into key-value pair: '{kv_pair_arg}")
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

            commands.append(Assignment(kv_pair=KeyValuePair(key=key, value=list_args)))

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
            commands.append(
                Assignment(
                    kv_pair=parse_kv_pair(arg, current_scope),
                )
            )

        index += 1
    return ParseResult(show=show, commands=commands)
