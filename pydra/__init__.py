from pathlib import Path

from pydra.cli import Alias, apply_overrides, main, run
from pydra.config import REQUIRED, Config
from pydra.utils import (
    DataclassWrapper,
    PydanticWrapper,
    load_binary,
    load_dill,
    load_pickle,
    load_yaml,
    save_dill,
    save_pickle,
    save_yaml,
)

version_file = Path(__file__).parent / "version.txt"
__version__ = version_file.read_text().strip()


__all__ = [
    "main",
    "run",
    "apply_overrides",
    "Alias",
    "Config",
    "REQUIRED",
    "load_dill",
    "load_pickle",
    "load_yaml",
    "load_binary",
    "save_dill",
    "save_pickle",
    "save_yaml",
    "DataclassWrapper",
    "PydanticWrapper",
]
