# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Activate venv
```bash
source .venv/bin/activate
```

### Testing
```bash
python -m unittest discover tests
```

### Installation
Development installation:
```bash
pip install -e .
```

Package installation from PyPI:
```bash
pip install pydra-config
```

## Project Architecture

Pydra is a Python configuration library inspired by Hydra, but using Python instead of YAML for configuration definitions. The core architecture consists of:

### Core Components

1. **Config System** (`pydra/config.py`): 
   - Base `Config` class that all configuration classes inherit from
   - Supports type annotations with automatic casting
   - Recursive finalization for nested configs
   - Built-in serialization to dict/YAML/pickle/dill

2. **Command Line Parser** (`pydra/parser.py`):
   - Parses command-line arguments into structured commands
   - Supports key-value assignments, method calls, scoping, and special flags
   - Handles various data types (int, float, str, bool, lists, Python expressions)

3. **CLI Interface** (`pydra/cli.py`):
   - Main `@pydra.main(ConfigClass)` decorator for scripts
   - `apply_overrides()` function for programmatic config modification
   - `run()` function for direct function execution with config inference
   - Alias support for alternative parameter names

4. **Utilities** (`pydra/utils.py`):
   - DataclassWrapper and PydanticWrapper for integrating external data structures
   - Serialization helpers (YAML, pickle, dill)
   - REQUIRED sentinel for mandatory configuration values

### Key Design Patterns

- **Nested Configuration**: Configs can contain other Config objects or dictionaries, accessible via dot notation
- **Method Calling**: Configuration objects can have methods callable from command line using `.method_name` syntax
- **Recursive Operations**: Finalization, validation, and serialization work recursively through nested structures
- **Type Safety**: Automatic type casting based on type annotations with support for Optional types
- **Scoping**: `--in` and `in--` commands allow temporary scoping of assignments to nested objects

### Command Line Features

The parser supports:
- Basic assignments: `key=value`
- Method calls: `.method_name` or `.method_name(args)`
- List creation: `--list key val1 val2 list--`
- Scoping: `--in nested_config key=value in--`
- Config display: `--show`
- Help display: `--help`
- Python expressions: `'key=(1+2*3)'`

### Version and Dependencies

- Current version: 0.0.15
- Python requirement: >=3.10
- Key dependencies: PyYAML, dill, pydantic