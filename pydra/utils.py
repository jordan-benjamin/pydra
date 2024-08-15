from pathlib import Path
import yaml
import dill
import pickle

from dataclasses import fields, MISSING

from copy import deepcopy


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


class DataclassWrapper:
    d: dict
    dataclass_type: type
    required_val: str

    def __init__(self, dataclass_type):
        param_dict = {}
        for field in fields(dataclass_type):
            if field.default is not MISSING:
                param_dict[field.name] = field.default
            else:
                param_dict[field.name] = REQUIRED

        self.__dict__["d"] = param_dict
        self.__dict__["dataclass_type"] = dataclass_type

    def build(self):
        for k, v in self.d.items():
            if v == REQUIRED:
                raise ValueError(
                    f"Missing required key '{k}' when instantiating dataclass {self.dataclass_type}"
                )

        config = self.dataclass_type(
            **self.d,
        )
        return config

    def __getattr__(self, key: str):
        try:
            return self.d[key]
        except KeyError:
            raise AttributeError(f"DataclassWrapper has no attribute '{key}'")

    def __getitem__(self, key):
        return self.d[key]

    def __setitem__(self, key, value):
        self.d[key] = value

    def __setattr__(self, key, value):
        if key not in self.d:
            raise ValueError(f"Trying to assign key that doesn't exist: '{key}'")
        self.d[key] = value

    def __deepcopy__(self, memodict={}):
        new_copy = type(self)(
            self.dataclass_type, deepcopy(self.required_val, memodict)
        )
        new_copy.__dict__["d"] = deepcopy(self.d, memodict)
        return new_copy

    def __repr__(self) -> str:
        return f"DataclassWrapper({self.d})"

    def __str__(self) -> str:
        return f"DataclassWrapper({self.d})"
