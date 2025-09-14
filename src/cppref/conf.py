import os
from pathlib import Path
from typing import Required, Self, TypedDict, cast

import toml

from cppref.typing_ import Source


class Configuration(TypedDict):
    source: Required[Source]


class ConfContext:
    STATE = Path(os.getenv("XDG_STATE_HOME") or "~/.local/state").expanduser()
    CACHE = Path(os.getenv("XDG_CACHE_HOME") or "~/.cache").expanduser()
    SHARE = Path(os.getenv("XDG_DATA_HOME") or "~/.local/share").expanduser()
    CONF = Path(os.getenv("XDG_CONFIG_HOME") or "~/.config").expanduser()

    def __init__(self) -> None:
        conf = ConfContext.conf_path()
        conf.parent.mkdir(parents=True, exist_ok=True)
        if conf.exists() and conf.is_file():
            self._conf = cast(Configuration, toml.load(conf))
            self._dirty = False
        else:
            root = ConfContext.man3_root()
            root.mkdir(parents=True, exist_ok=True)
            self._conf = Configuration(source="cppreference")
            self._dirty = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, __1__, __2__, __3__):
        if not self._dirty:
            return False
        with open(ConfContext.conf_path(), "w", encoding="utf-8") as file:
            toml.dump(self._conf, file)
        return False

    @property
    def source(self) -> Source:
        return self._conf["source"]

    @source.setter
    def source(self, source: Source):
        self._conf["source"] = source
        self._dirty = True

    @staticmethod
    def dbfile() -> Path:
        return ConfContext.SHARE.joinpath("cppref", "index.db")

    @staticmethod
    def conf_path() -> Path:
        return ConfContext.CONF.joinpath("cppref", "conf.toml")

    @staticmethod
    def man3_root() -> Path:
        return ConfContext.SHARE.joinpath("man", "man3")

    @staticmethod
    def html_root() -> Path:
        return ConfContext.CACHE.joinpath("cppref")

    @staticmethod
    def read_source() -> Source:
        with ConfContext() as conf:
            return conf.source
