import os
from pathlib import Path
from typing import Self, cast

import toml

from cppref.typing_ import Configuration, Source


class ConfContext:
    def __init__(self) -> None:
        state = Path(os.getenv("XDG_STATE_HOME") or "~/.local/state").expanduser()
        share = Path(os.getenv("XDG_DATA_HOME") or "~/.local/share").expanduser()
        path: Path = state.joinpath("cppref", "conf.toml")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.is_file():
            self._conf = cast(Configuration, toml.load(path))
            self._dirty = False
        else:
            root = share.joinpath("cppref")
            root.mkdir(parents=True, exist_ok=True)
            self._conf = Configuration(source="cppreference", folder=str(root))
            self._dirty = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, __1__, __2__, __3__):
        if not self._dirty:
            return False
        state = Path(os.getenv("XDG_STATE_HOME") or "~/.local/state").expanduser()
        path: Path = state.joinpath("cppref", "conf.toml")
        with open(path, "w", encoding="utf-8") as file:
            toml.dump(self._conf, file)
        return False

    @property
    def source(self) -> Source:
        return self._conf["source"]

    @source.setter
    def source(self, source: Source):
        self._conf["source"] = source
        self._dirty = True

    @property
    def folder(self) -> Path:
        return Path(self._conf["folder"]).expanduser().absolute()

    @folder.setter
    def folder(self, folder: Path):
        self._conf["folder"] = str(folder.expanduser().absolute())
        self._dirty = True

    @property
    def dbfile(self) -> Path:
        return self.folder.joinpath("index.db")
