import unittest
from pathlib import Path


class TestBase(unittest.TestCase):
    @staticmethod
    def get_root():
        path = Path(__file__).resolve().absolute().parent
        while not path.joinpath("pyproject.toml").exists():
            path = path.parent
        return path
