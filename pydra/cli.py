import sys
import yaml

from dataclasses import dataclass

from typing import Optional
from pydra.config import Config
import pydra.parser


@dataclass
class Alias:
    name: str


def assign(obj, key: str, value, assert_exists: bool = True):
    split_dots = key.split(".")

    obj_path = [obj]
    for i, k in enumerate(split_dots):
        cur_obj = obj_path[-1]

        if isinstance(cur_obj, dict):
            has_func = lambda o, k: k in o
            get_func = lambda o, k: o[k]
            set_func = lambda o, k, v: o.update({k: v})
        else:
            has_func = hasattr
            get_func = getattr
            set_func = setattr

        if has_func(cur_obj, k):
            next_obj = get_func(cur_obj, k)
            if isinstance(next_obj, Alias):
                k = next_obj.name

        # at our destination
        if i == len(split_dots) - 1:
            if assert_exists and not has_func(cur_obj, k):
                raise AttributeError(f"Config does not have attribute {key}")

            set_func(cur_obj, k, value)
        else:
            if not assert_exists and not has_func(cur_obj, k):
                set_func(cur_obj, k, {})
            new_obj = get_func(cur_obj, k)
            obj_path.append(new_obj)


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
                assert_exists=command.assert_exists,
            )
        elif isinstance(command, pydra.parser.MethodCall):
            getattr(config, command.method_name)(*command.args, **command.kwargs)
        else:
            raise ValueError(f"Unknown command type {command}")

    if enforce_required:
        config._enforce_required()

    if finalize:
        config.finalize()

    return parsed_args.show


# makes the decorator
def main(base: type[Config]):
    def decorator(fn):

        def wrapped_fn(config: Optional[Config] = None):
            # allow other scripts to call the wrapped function directly
            if config is not None:
                return fn(config)

            args = sys.argv[1:]

            config = base()

            show = apply_overrides(config, args, finalize=True)

            if show:
                print(yaml.dump(config.to_dict(), sort_keys=True))
                return

            return fn(config)

        return wrapped_fn

    return decorator
