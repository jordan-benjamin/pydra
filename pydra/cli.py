import inspect
import sys
from dataclasses import dataclass
from typing import Callable, Type, TypeVar

import yaml

import pydra.parser
from pydra.config import Config


@dataclass
class Alias:
    name: str


def drill_through_objects(obj, key: str):
    split_dots = key.split(".")

    obj_path = [obj]
    for i, k in enumerate(split_dots):
        cur_obj = obj_path[-1]

        def has_func(o, k):
            if isinstance(o, dict):
                return k in o
            else:
                return hasattr(o, k)

        def get_func(o, k):
            if isinstance(o, dict):
                return o[k]
            else:
                return getattr(o, k)

        if has_func(cur_obj, k):
            next_obj = get_func(cur_obj, k)
            if isinstance(next_obj, Alias):
                k = next_obj.name

        if not has_func(cur_obj, k):
            raise AttributeError(
                f"Config does not have attribute '{key}' (failed at '{'.'.join(split_dots[:i + 1])}')"
            )

        # at our destination
        if i == len(split_dots) - 1:
            return cur_obj, k
        else:
            new_obj = get_func(cur_obj, k)
            obj_path.append(new_obj)


def assign(obj, key: str, value):
    drilled_obj, k = drill_through_objects(obj, key)

    match drilled_obj:
        case dict():
            drilled_obj[k] = value
        case Config():
            drilled_obj._assign_maybe_cast(k, value)
        case _:
            setattr(drilled_obj, k, value)


def apply_overrides(
    config: Config,
    args: list[str],
    enforce_required: bool = True,
    finalize: bool = True,
) -> bool:
    parsed_args = pydra.parser.parse(args)

    for command in parsed_args.commands:
        if isinstance(command, pydra.parser.Assignment):
            assign(
                config,
                command.kv_pair.key,
                command.kv_pair.value,
            )
        elif isinstance(command, pydra.parser.MethodCall):
            drilled_obj, drilled_method_name = drill_through_objects(
                config, command.method_name
            )
            method = getattr(drilled_obj, drilled_method_name)
            method(*command.args, **command.kwargs)
        else:
            raise ValueError(f"Unknown command type {command}")

    if enforce_required:
        config._enforce_required()

    if finalize:
        config._recursive_finalize()

    return parsed_args.show


# SE (02/24/25): Using the old generic class syntax for compatibility with Python <3.12
T = TypeVar("T", bound=Config)
U = TypeVar("U")


def _apply_overrides_and_call(
    fn: Callable[[T], U], config_t: Type[T], args: list[str] | None = None
):
    config = config_t()

    if args is None:
        args = sys.argv[1:]

    show = apply_overrides(config, args, finalize=True)

    if show:
        print(yaml.dump(config.to_dict(), sort_keys=True))
        return

    return fn(config)


def main(base: Type[T]):
    def decorator(fn: Callable[[T], U]):
        def wrapped_fn(args: list[str] | None = None):
            return _apply_overrides_and_call(fn, base, args)

        return wrapped_fn

    return decorator


def run(fn: Callable[[T], U], args: list[str] | None = None):
    signature = inspect.signature(fn)
    params = signature.parameters

    if len(params) != 1:
        raise ValueError(f"Function '{fn}' must take in one argument")

    first_arg_type = list(params.values())[0].annotation

    # assert arg is instance of Config
    if not issubclass(first_arg_type, Config):
        raise ValueError(
            f"Type annotation of function argument must be a subclass of Config, but got {first_arg_type}"
        )

    return _apply_overrides_and_call(fn, first_arg_type, args)
