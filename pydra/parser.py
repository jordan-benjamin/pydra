from dataclasses import dataclass, field
from typing import Any, Union, List, Dict
import ast

@dataclass
class KeyValuePair:
    key: str
    value: Any

@dataclass
class MethodCall:
    method_name: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Assignment:
    kv_pair: KeyValuePair

@dataclass
class ParseResult:
    show: bool
    commands: List[Union[Assignment, MethodCall]]

# builtin functions don't handle whitespace
def isfloat(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def isint(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_string_literal(value: str) -> bool:
    for char in ['"', "'"]:
        if value.startswith(char) and value.endswith(char):
            return True
    return False


def drop_first_last(value: str) -> str:
    return value[1:-1]


def parse_value(value: str) -> Any:
    
    # --- AST-based Python parsing for curly-brace expressions ---
    if value.startswith("{") and value.endswith("}"):
        expr = value[1:-1]
        try:
            # safely parse Python literals
            return ast.literal_eval(expr)
        except Exception:
            return eval(expr)
    # ----------------------------------------------------------------

    if is_string_literal(value):
        return drop_first_last(value)
    elif isint(value):
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
        between = drop_first_last(value)
        if not between:
            return []
        return [parse_value(x.strip()) for x in between.split(",")]
    elif value.startswith("(") and value.endswith(")"):
        inner = drop_first_last(value)
        return eval(inner)
    else:
        return value


def scope_key(scope: list[str], key: str) -> str:
    return key if not scope else ".".join(scope + [key])


def parse_kv_pair(kv_pair_arg: str, scope: list[str]) -> KeyValuePair:
    """Parse a string of the form 'key=value'"""
    if "=" not in kv_pair_arg:
        raise ValueError(f"Couldn't parse into key=value: '{kv_pair_arg}'")
    key, val = kv_pair_arg.split("=", 1)
    return KeyValuePair(scope_key(scope, key), parse_value(val))


def parse(args: List[str]) -> ParseResult:
    current_scope: List[str] = []
    show = False
    index = 0
    commands: List[Union[Assignment, MethodCall]] = []

    while index < len(args):
        arg = args[index]
        if arg == "--show":
            show = True
        elif arg == "--list":
            # next item is key
            key = args[index + 1]
            index += 2
            items: List[Any] = []
            while args[index] != "list--":
                items.append(parse_value(args[index]))
                index += 1
            commands.append(Assignment(kv_pair=KeyValuePair(key=key, value=items)))
        elif arg == "--in":
            current_scope.append(args[index + 1])
            index += 1
        elif arg == "in--":
            current_scope.pop()
        elif arg.startswith("."):
            # method invocation
            if "(" in arg and arg.endswith(")"):
                name = arg[1:arg.index("(")]
                contents = arg[arg.index("(") + 1 : -1]
                parts = [p.strip() for p in contents.split(",") if p.strip()]
                m_args: List[Any] = []
                m_kwargs: Dict[str, Any] = {}
                for part in parts:
                    if "=" in part:
                        kv = parse_kv_pair(part, [])
                        m_kwargs[kv.key] = kv.value
                    else:
                        if m_kwargs:
                            raise ValueError(f"Positional argument {part} after keyword arguments in method {name}")
                        m_args.append(parse_value(part))
                commands.append(MethodCall(method_name=name, args=m_args, kwargs=m_kwargs))
            else:
                commands.append(MethodCall(method_name=arg[1:]))
        else:
            commands.append(Assignment(kv_pair=parse_kv_pair(arg, current_scope)))
        index += 1
    return ParseResult(show=show, commands=commands)



if __name__ == "__main__":
    demo_args = [
        "--show",
        "x=10",
        "y={1, 2, 3}",
        "--in", "scope",
        "nested_val={ {'a': 1, 'b': [4,5]} }",
        "in--",
        ".print()",
        "--list", "nums", "1", "2", "{3+4}", "list--"
    ]
    result = parse(demo_args)
    print("Show flag:", result.show)
    for cmd in result.commands:
        print(cmd)
