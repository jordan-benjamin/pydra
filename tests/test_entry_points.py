import unittest

from pydra import Config, main, run


class SimpleConfig(Config):
    def __init__(self):
        self.x = 1
        self.y = 2


def undecorated_fn(config: SimpleConfig):
    return config.x * config.y + 1


@main(SimpleConfig)
def decorated_fn(config: SimpleConfig):
    return undecorated_fn(config)


class TestEntryPoints(unittest.TestCase):
    def test_run(self):
        result = run(undecorated_fn, ["x=5"])
        self.assertEqual(result, 11)

    def test_main(self):
        result = decorated_fn(["x=5", "y=3"])
        self.assertEqual(result, 16)
