import pickle
from copy import deepcopy
from dataclasses import MISSING, fields
from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar

import dill
import yaml
from pydantic import BaseModel

if TYPE_CHECKING:
    from _typeshed import DataclassInstance


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


T = TypeVar("T")


class BaseWrapper(Generic[T]):
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


if TYPE_CHECKING:
    DataclassInstanceT = TypeVar("DataclassInstanceT", bound=DataclassInstance)
else:
    DataclassInstanceT = TypeVar("DataclassInstanceT")


class DataclassWrapper(BaseWrapper[DataclassInstanceT]):
    def __init__(self, wrapped_type: type["DataclassInstanceT"]):
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


BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


class PydanticWrapper(BaseWrapper[BaseModelT]):
    def __init__(self, wrapped_type: type[BaseModelT]):
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


def generate_help_text(config_class) -> str:
    """Generate help text for a Config class by inspecting its structure."""
    from pydra.config import Config, get_annotations
    import inspect
    
    def format_value(val):
        if val is REQUIRED:
            return "REQUIRED"
        elif val is None:
            return "None"
        elif isinstance(val, str):
            return f'"{val}"'
        elif isinstance(val, (list, tuple)):
            return str(val)
        elif isinstance(val, dict):
            return str(val)
        else:
            return str(val)
    
    def collect_config_info(config_obj, prefix=""):
        """Recursively collect information about config fields."""
        info = []
        annotations = get_annotations(config_obj.__class__)
        
        for attr_name in dir(config_obj):
            if attr_name.startswith('_'):
                continue
                
            try:
                attr_value = getattr(config_obj, attr_name)
            except:
                continue
                
            # Skip methods that aren't part of the config
            if callable(attr_value):
                # Skip built-in methods and finalize
                built_in_methods = {'finalize', 'save_dill', 'save_pickle', 'save_yaml', 'to_dict', '_enforce_required', '_recursive_finalize', '_assign_maybe_cast'}
                if attr_name in built_in_methods or attr_name.startswith('_'):
                    continue
                    
                if hasattr(config_obj.__class__, attr_name):
                    method = getattr(config_obj.__class__, attr_name)
                    if inspect.isfunction(method) or inspect.ismethod(method):
                        try:
                            sig = inspect.signature(method)
                            params = list(sig.parameters.keys())[1:]  # Skip 'self'
                            if params:
                                param_str = f"({', '.join(params)})"
                            else:
                                param_str = "()"
                            full_name = f"{prefix}.{attr_name}{param_str}" if prefix else f".{attr_name}{param_str}"
                            info.append((full_name, "method", "Call this method"))
                        except:
                            pass
                continue
            
            # Skip built-in attributes that aren't actual config fields
            built_in_attrs = {'finalize', 'save_dill', 'save_pickle', 'save_yaml', 'to_dict', '_enforce_required', '_recursive_finalize', '_assign_maybe_cast', '_init_annotations'}
            if attr_name in built_in_attrs or attr_name.startswith('_'):
                continue
            
            # Handle config fields
            full_name = f"{prefix}.{attr_name}" if prefix else attr_name
            
            # Get type annotation if available
            type_info = ""
            if attr_name in annotations:
                type_info = f" ({annotations[attr_name].__name__})"
            
            # Handle nested configs
            if isinstance(attr_value, Config):
                info.append((full_name, "config", f"Nested configuration{type_info}"))
                info.extend(collect_config_info(attr_value, full_name))
            elif isinstance(attr_value, (DataclassWrapper, PydanticWrapper)):
                info.append((full_name, "wrapper", f"Wrapped object: {attr_value.wrapped_type.__name__}{type_info}"))
                # Add wrapper fields
                for field_name, field_value in attr_value.d.items():
                    field_full_name = f"{full_name}.{field_name}"
                    info.append((field_full_name, "field", f"Default: {format_value(field_value)}{type_info}"))
            elif isinstance(attr_value, dict):
                info.append((full_name, "dict", f"Dictionary, default: {format_value(attr_value)}{type_info}"))
            else:
                info.append((full_name, "field", f"Default: {format_value(attr_value)}{type_info}"))
        
        return info
    
    # Create temporary instance to inspect
    try:
        temp_config = config_class()
    except Exception as e:
        return f"Error creating config instance for help: {e}"
    
    config_info = collect_config_info(temp_config)
    
    if not config_info:
        return f"No configurable options found for {config_class.__name__}"
    
    # Format the help text
    lines = [f"Configuration options for {config_class.__name__}:", ""]
    
    # Group by type
    fields = [item for item in config_info if item[1] == "field"]
    methods = [item for item in config_info if item[1] == "method"]
    configs = [item for item in config_info if item[1] in ["config", "wrapper"]]
    dicts = [item for item in config_info if item[1] == "dict"]
    
    if fields:
        lines.append("Fields:")
        for name, _, desc in fields:
            lines.append(f"  {name:<30} {desc}")
        lines.append("")
    
    if dicts:
        lines.append("Dictionaries:")
        for name, _, desc in dicts:
            lines.append(f"  {name:<30} {desc}")
        lines.append("")
    
    if configs:
        lines.append("Nested configurations:")
        for name, _, desc in configs:
            lines.append(f"  {name:<30} {desc}")
        lines.append("")
    
    if methods:
        lines.append("Available methods:")
        for name, _, desc in methods:
            lines.append(f"  {name:<30} {desc}")
        lines.append("")
    
    lines.extend([
        "Usage examples:",
        "  python script.py field_name=value",
        "  python script.py nested.field=value",
        "  python script.py .method_name",
        "  python script.py .method_name(arg1,arg2)",
        "  python script.py --list field_name val1 val2 list--",
        "  python script.py --show  # Display final configuration",
        ""
    ])
    
    return "\n".join(lines)
