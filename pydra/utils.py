from pathlib import Path
import yaml
import dill
import pickle

from dataclasses import fields, MISSING

from copy import deepcopy
from pydantic import BaseModel


class _Required:
    pass


REQUIRED = _Required()

# https://stackoverflow.com/questions/6432605/any-yaml-libraries-in-python-that-support-dumping-of-long-strings-as-block-liter


class literal_unicode(str):
    pass


def literal_unicode_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.add_representer(literal_unicode, literal_unicode_representer)


def transform_into_literals(data):
    if isinstance(data, dict):
        data = {k: transform_into_literals(v) for k, v in data.items()}
        return data
    elif isinstance(data, list):
        return [transform_into_literals(x) for x in data]
    elif isinstance(data, str):
        if "\n" in data:
            return literal_unicode(data)
        else:
            return data
    else:
        return data


def load_yaml(path: Path):
    with open(path, "r") as f:
        data = yaml.load(f, Loader=yaml.CLoader)

    return data


def save_yaml(data, path: Path, sort_keys=True, transform=True):
    if transform:
        data = transform_into_literals(data)

    with open(path, "w") as f:
        yaml.dump(
            data,
            f,
            sort_keys=sort_keys,
        )


def load_dill(path: Path):
    with open(path, "rb") as f:
        data = dill.load(f)

    return data


def save_dill(data, path: Path):
    with open(path, "wb") as f:
        dill.dump(data, f)


def load_pickle(path: Path):
    with open(path, "rb") as f:
        data = pickle.load(f)

    return data


def save_pickle(data, path: Path):
    with open(path, "wb") as f:
        pickle.dump(data, f)


def load_binary(path: Path):
    if path.suffix == ".dill":
        return load_dill(path)
    elif path.suffix == ".pkl":
        return load_pickle(path)
    else:
        raise ValueError(f"Unknown extension {path.suffix}")


class BaseWrapper[T]:
    d: dict
    wrapped_type: type[T]

    def __init__(self, wrapped_type: type[T]):
        raise NotImplementedError

    def build(self):
        for k, v in self.d.items():
            if v == REQUIRED:
                raise ValueError(
                    f"Missing required key '{k}' when instantiating wrapped type {self.wrapped_type}"
                )

        config = self.wrapped_type(**self.d)
        return config

    def spoof(self) -> T:
        """
        This is a hack for IDE type checking, allowing us
        to assign to fields in this wrapper class as if it
        was an instance of the wrapped type.
        """
        return self  # type: ignore

    def __deepcopy__(self, memodict={}):
        new_copy = type(self)(self.wrapped_type)
        new_copy.__dict__["d"] = deepcopy(self.d, memodict)
        return new_copy

    def __repr__(self) -> str:
        return f"{self.wrapped_type.__name__}({self.d})"

    def __str__(self) -> str:
        return f"{self.wrapped_type.__name__}({self.d})"

    def __getstate__(self):
        return {"d": self.d, "wrapped_type": self.wrapped_type}

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __getattr__(self, key: str):
        try:
            return self.d[key]
        except KeyError:
            raise AttributeError(
                f"{self.wrapped_type.__name__} has no attribute '{key}'"
            )

    def __getitem__(self, key):
        return self.d[key]

    def __setitem__(self, key, value):
        self.d[key] = value

    def __setattr__(self, key, value):
        if key not in self.d:
            raise ValueError(f"Trying to assign key that doesn't exist: '{key}'")
        self.d[key] = value


class DataclassWrapper[T](BaseWrapper[T]):
    def __init__(self, wrapped_type: type[T]):
        param_dict = {}
        for field in fields(wrapped_type):
            if field.default is not MISSING:
                param_dict[field.name] = field.default
            elif field.default_factory is not MISSING:
                param_dict[field.name] = field.default_factory()
            else:
                param_dict[field.name] = REQUIRED

        self.__dict__["d"] = param_dict
        self.__dict__["wrapped_type"] = wrapped_type


class PydanticWrapper[T: BaseModel](BaseWrapper[T]):
    def __init__(self, wrapped_type: type[T]):
        param_dict = {}
        for field_name, field_info in wrapped_type.model_fields.items():
            if field_info.default is not None:
                param_dict[field_name] = field_info.default
            elif field_info.default_factory is not None:
                param_dict[field_name] = field_info.default_factory()
            else:
                param_dict[field_name] = REQUIRED

        self.__dict__["d"] = param_dict
        self.__dict__["wrapped_type"] = wrapped_type
