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

def split_top_level(s: str) -> List[str]:
    parts = []
    current = []
    depth = 0
    brackets = {'(': ')', '[': ']', '{': '}'}
    opens = brackets.keys()
    closes = brackets.values()
    matching = {v: k for k, v in brackets.items()}
    for char in s:
        if char in opens:
            depth += 1
        elif char in closes:
            depth -= 1
        if char == ',' and depth == 0:
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)
    if current:
        parts.append(''.join(current))
    return parts

# builtin helpers
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
    return (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'"))


def drop_first_last(value: str) -> str:
    return value[1:-1]


def parse_value(value: str) -> Any:
    # --- AST-based Python parsing for curly-brace expressions ---
    if value.startswith("{") and value.endswith("}"):
        full = value
        inner = value[1:-1]
        # 1. full literal (set, dict)
        try:
            return ast.literal_eval(full)
        except (ValueError, SyntaxError, TypeError):
            pass
        # 2. eval on full (for comprehensions)
        try:
            return eval(full)
        except Exception:
            pass
        # 3. literal_eval on inner (fallback to list/dict literal)
        try:
            return ast.literal_eval(inner)
        except (ValueError, SyntaxError, TypeError):
            pass
        # 4. eval on inner (expressions)
        try:
            return eval(inner)
        except Exception:
            return value

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
        items = split_top_level(between)
        return [parse_value(x.strip()) for x in items]
    elif value.startswith("(") and value.endswith(")"):
        inner = drop_first_last(value)
        try:
            return eval(inner)
        except Exception:
            return inner
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
                parts = split_top_level(contents)
                m_args: List[Any] = []
                m_kwargs: Dict[str, Any] = {}
                for part in [p.strip() for p in parts if p.strip()]:
                    if "=" in part:
                        kv = parse_kv_pair(part, [])
                        m_kwargs[kv.key] = kv.value
                    else:
                        if m_kwargs:
                            raise ValueError(
                                f"Positional argument {part} after keyword arguments in method {name}"
                            )
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
