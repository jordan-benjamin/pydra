from pydra.utils import save_yaml, save_dill, save_pickle, DataclassWrapper, REQUIRED
from pathlib import Path
import inspect
from types import UnionType, NoneType
from typing import get_args, get_origin, Union


class Config:
    def _init_annotations(self):
        cls = self.__class__
        # get the class' type annotations
        annotations = inspect.get_annotations(cls)

        for name, _ in annotations.items():
            init_value = getattr(cls, name, REQUIRED)
            setattr(self, name, init_value)

    def _assign_maybe_cast(self, key: str, value):
        annotations = inspect.get_annotations(self.__class__)
        if ann_type := annotations.get(key):
            # handling for the optionals of the form Optional[T] or T | None
            if get_origin(ann_type) in [Union, UnionType]:
                type_args = get_args(ann_type)
                if len(type_args) != 2 or type_args[1] != NoneType:
                    raise ValueError(
                        f"Can only support union types of the form Optional[T] or T | None, but got '{ann_type}'"
                    )

                inner_type = type_args[0]

                if value is None:
                    pass
                else:
                    value = inner_type(value)

            else:
                value = ann_type(value)

        setattr(self, key, value)

    def finalize(self):
        pass

    def to_dict(self):
        data = {}

        for k, v in self.__dict__.items():
            if isinstance(v, DataclassWrapper):
                v = v.d

            if isinstance(v, Config):
                data[k] = v.to_dict()
            elif isinstance(v, (list, tuple)):
                data[k] = [x.to_dict() if isinstance(x, Config) else x for x in v]
            elif isinstance(v, dict):
                data[k] = {
                    k: v.to_dict() if isinstance(v, Config) else v for k, v in v.items()
                }
            elif isinstance(v, (int, float, str, bool)):
                data[k] = v
            else:
                data[k] = str(v)

        return data

    def save_yaml(self, path: Path):
        data = self.to_dict()
        save_yaml(data, path)

    def save_dill(self, path: Path):
        save_dill(self, path)

    def save_pickle(self, path: Path):
        save_pickle(self, path)

    def _enforce_required(self):
        for k, v in self.__dict__.items():
            if v is REQUIRED:
                raise ValueError(f"Missing required config value: {k}")
            elif isinstance(v, Config):
                v._enforce_required()
            elif isinstance(v, (list, tuple)):
                for x in v:
                    if isinstance(x, Config):
                        x._enforce_required()
            elif isinstance(v, dict):
                for k2, v2 in v.items():
                    if isinstance(v2, Config):
                        v2._enforce_required()
