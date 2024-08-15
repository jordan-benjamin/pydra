# Pydra

## What is This?

Pydra is a Python configuration library. The project is heavily inspired by [Hydra](https://hydra.cc/), which provides helpful command-line overrides and allows for a lot of flexiblity. While Hydra uses YAML as a config definition language (which can be unwieldly to work with), Pydra uses Python. The goal of the project is to let you write your configs in the same language that your code is in, while trying to keep the same level of flexibility and ease-of-use.

## Installation

To install the latest release from PyPI:

```bash
pip install pydra-config
```

Or to install from source, clone the repo, `cd` into it, and run:

```bash
pip install -e .
```

# Usage

## The Basics

Like Hydra, Pydra has a main decorator that you use to wrap your script's entry point. However, while the Hydra main is parameterized by the path to a YAML file/directory, Pydra uses a config class. Here's an example:

```python
import pydra

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.foo = 5
        self.bar = None

@pydra.main(MyConfig)
def main(config: MyConfig):
    print(f"foo: {config.foo}")
    print(f"bar: {config.bar}")

if __name__ == "__main__":
    main()
```

You can run this script with:

```bash
python script.py

python script.py foo=10 bar=20
```

Pydra will parse several different types, such as:

```bash
python script.py foo=10  # int
python script.py foo=3.14  # float
python script.py foo=hello  # str
python script.py foo=True  # bool (also accepts "T")
python script.py foo=None  # None
python script.py 'foo=[1,2,3]'  # list of ints
python script.py 'foo=(1+3 * (2 ** 3))' # arbitrary python expression (uses eval())

python script.py baz=1 # will crash, field does not exist
python script.py +baz=1 # adds a new field
```

## Method Calling

Since Pydra configs are proper Python objects, Pydra allows you to call methods on them directly from the command line. This is particularly useful for modifying the configuration in more complex ways.

```python
import pydra

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.value = 0

    def increment(self, amount=1):
        self.value += amount

    def reset(self):
        self.value = 0


@pydra.main(MyConfig)
def main(config: MyConfig):
    print(f"Final value: {config.value}")

if __name__ == "__main__":
    main()
```

You can call these methods from the command line like this:

```bash
python script.py .increment  # Calls increment() with default argument
python script.py '.increment(amount=5)'  # Calls increment(amount=5)
python script.py .reset  # Calls reset()
```

You can also chain multiple method calls and assignments:

```bash
python script.py '.increment(amount=3)' .increment value=10 .reset
```

This will increment by 3, then increment by 1 (default), set value to 10, and finally reset to 0.

## `finalize()`

The `finalize()` method is a special method in your config class that is called after all command-line arguments have been processed. This is useful for performing any final setup, validation, or derived calculations based on the input parameters.

```python
import pydra

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.x = 1
        self.y = 2

    def finalize(self):
        self.sum = self.x + self.y

@pydra.main(MyConfig)
def main(config: MyConfig):
    print(f"x: {config.x}, y: {config.y}, sum: {config.sum}")

if __name__ == "__main__":
    main()
```

## Nested Configs

Configs can contain dictionaries or other Config objects.

```python
import pydra

class InnerConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.x = 1
        self.y = 2

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.inner = InnerConfig()
        self.d = {"a": 3, "b": 4}


@pydra.main(MyConfig)
def main(config: MyConfig):
    print(f"Inner x: {config.inner.x}")
    print(f"Inner y: {config.inner.y}")
    print(f"Dict a: {config.d['a']}")
    print(f"Dict b: {config.d['b']}")

if __name__ == "__main__":
    main()
```

You can access nested fields from the command line using dots:

```bash
python script.py inner.x=5 d.a=10
```

## `--in`

You can also temporarily scope your assignments to a nested config using the `--in` flag. Use `in--` to end the scoping region. Using the above example:

```bash
python script.py --in inner x=5 y=10 in-- --in d a=100 b=101 in--
```

## Required Variables

Pydra supports marking certain configuration variables as required. If a required variable is not set, Pydra will raise an error.

```python
import pydra

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.optional = 5
        self.required = pydra.REQUIRED

@pydra.main(MyConfig)
def main(config: MyConfig):
    print(f"Optional: {config.optional}")
    print(f"Required: {config.required}")

if __name__ == "__main__":
    main()
```

Running this script without setting the required variable will result in an error:

```bash
python script.py  # Error: Required variable 'required' not set
python script.py required=10  # This will work
```

## `--list`

Often it can be handy to make a list using space delimiters. Pydra supports this with the `--list` flag.

```python
import pydra

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.x = None
        self.y = 1

@pydra.main(MyConfig)
def main(config: MyConfig):
    print(f"x: {config.x}")
    print(f"y: {config.y}")

if __name__ == "__main__":
    main()
```


```bash
python script.py --list x 1 2 3 list-- y=4

# This is equivalent to
python script.py 'x=[1,2,3]' y=4
```

## `--show`

Pass the `--show` flag at any point on the command line to print out the configuration (after applying all overrides and calling `finalize`) and then end the program. Using the above example:

```bash
python script.py --list x 1 2 3 list-- y=4 --show
```

## Aliases

Aliases in Pydra allow you to create alternative names for configuration variables. This can be useful for creating shortcuts or more intuitive command-line interfaces.

```python
import pydra

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.very_long_variable_name = 42
        self.short = pydra.Alias("very_long_variable_name")

@pydra.main(MyConfig)
def main(config: MyConfig):
    print(f"Value: {config.very_long_variable_name}")

if __name__ == "__main__":
    main()
```

You can now use either the original name or the alias on the command line:

```bash
python script.py very_long_variable_name=100
# or
python script.py short=100
```

Both will set the same variable.

## Working with Data Classes

Pydra also supports incorporating data classes into configs. Use `pydra.DataclassWrapper` to create an object that you can assign into from the CLI. Call `build()` on the object to get the dataclass instance.

```python
import pydra
from dataclasses import dataclass

@dataclass
class InnerConfig:
    x: int
    y: int
    z: int = 11

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.dc = pydra.DataclassWrapper(InnerConfig)


@pydra.main(MyConfig)
def main(config: MyConfig):
    dc = config.dc.build()
    print("dc", dc)

if __name__ == "__main__":
    main()
```

Pydra will prevent you from setting dataclass fields that don't exist, and make sure that all required fields are set.

```bash
python script.py dc.x=5 dc.y=10 # good
python script.py dc.z=20 dc.y=10 dc.x=5 # also good
python script.py dc.x=5 # error, missing required field y
python script.py dc.x=5 dc.w=30 # error, w is not a field
```

## Serializing Configs

To produce a human-readable serialization of your config, you can use the `to_dict()` method. We also provide a few helper functions to save configs to YAML, pickle, or dill files.

```python
import pydra

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.x = 5
        self.y = 10

@pydra.main(MyConfig)
def main(config: MyConfig):
    as_dict = config.to_dict()
    print(as_dict)

    pydra.save_yaml(as_dict, "conf.yaml")
    pydra.save_pickle(as_dict, "conf.pkl")
    pydra.save_dill(as_dict, "conf.dill")

if __name__ == "__main__":
    main()
```

## Pydra without `main`

You can also apply Pydra overrides programmatically with `apply_overrides`, which takes in a `Config` instance and a list of args.

```python
import pydra

class MyConfig(pydra.Config):
    def __init__(self):
        super().__init__()
        self.x = 5
        self.y = 10


config = MyConfig()
pydra.apply_overrides(config, ["x=20", "y=30"])

print(config.to_dict())
```

# Running Tests

To run the repo's test suite, use:

```bash
python -m unittest discover tests
```