import asyncio
import os
import unittest
from unittest.mock import patch

from cppref.conf import ConfContext
from cppref.utils import Utils
from tests.helpers import get_root


class UtilsTest(unittest.TestCase):
    def setUp(self) -> None:
        root = get_root().joinpath("testdata")
        root.mkdir(parents=True, exist_ok=True)
        state = root.joinpath("state")
        cache = root.joinpath("share")
        state.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)
        self._environs = {"XDG_STATE_HOME": str(state), "XDG_DATA_HOME": str(cache)}

    def test_query(self):
        share = get_root().expanduser().absolute().joinpath("testdata", "share")
        with patch.dict(os.environ, self._environs):
            with ConfContext() as conf:
                folder = conf.folder
                # dbfile for test is not the same as actual index.db used
                dbfile = get_root().joinpath("testdata", "index.db")

        self.assertEqual(folder, share.joinpath("cppref"))
        self.assertTrue(dbfile.exists() and dbfile.is_file())
        records = Utils.query("cppreference", dbfile)
        self.assertEqual(len(records), 6027)
        self.assertEqual(records[0].id, 1)
        self.assertEqual(records[0].title, "C++ reference")
        records = Utils.query("cplusplus", dbfile)
        self.assertEqual(len(records), 3027)
        self.assertEqual(records[0].id, 1)
        self.assertEqual(records[0].title, "Reference")

    def test_fetch(self):
        dbfile = get_root().joinpath("testdata", "index.db")

        record = Utils.query("cppreference", dbfile)[0]
        webpage = Utils.fetch(record, 10)
        self.assertTrue(webpage.startswith("<!DOCTYPE html>\n<html"))

    def test_afetch(self):
        dbfile = get_root().joinpath("testdata", "index.db")
        record = Utils.query("cppreference", dbfile)[0]

        async def task():
            async for webpage in Utils.afetch(record, timeout=10, limit=10):
                return webpage

        webpage = asyncio.run(task())
        self.assertTrue(isinstance(webpage, str) and webpage.startswith("<!DOCTYPE html>\n<html"))  # fmt: off
