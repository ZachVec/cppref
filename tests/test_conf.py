import os
from unittest.mock import patch

from cppref.conf import ConfContext
from tests.helpers import TestBase


class ConfigurationTest(TestBase):
    def setUp(self) -> None:
        root = self.get_root().joinpath("testdata")
        root.mkdir(parents=True, exist_ok=True)
        state = root.joinpath("state")
        cache = root.joinpath("share")
        state.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)
        self._environs = {"XDG_STATE_HOME": str(state), "XDG_DATA_HOME": str(cache)}

    def test_generation(self):
        root = self.get_root().expanduser().absolute().joinpath("testdata")
        share = root.joinpath("share", "cppref")
        with patch.dict(os.environ, self._environs):
            with ConfContext() as conf:
                self.assertEqual(conf.folder, share)
                self.assertEqual(conf.dbfile, share.joinpath("index.db"))
            conf = root.joinpath("state", "cppref", "conf.toml")
            self.assertTrue(conf.exists() and conf.is_file())

    def test_update(self):
        with patch.dict(os.environ, self._environs):
            with ConfContext() as conf:
                original = conf.source
                conf.source = "cppreference"

            with ConfContext() as conf:
                self.assertEqual(conf.source, "cppreference")
                conf.source = "cplusplus"

            with ConfContext() as conf:
                self.assertEqual(conf.source, "cplusplus")
                conf.source = original
