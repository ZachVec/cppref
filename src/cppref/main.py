from __future__ import annotations

import asyncio
import os
import sqlite3
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Optional, Sequence, overload, cast

import toml
from httpx import AsyncClient, Client, Headers, Limits

from cppref.typing_ import ConfKey, ConfVal, Record, Source

HEADERS = Headers()
HEADERS.setdefault(
    "User-Agent",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0",
)


class Utils:
    @staticmethod
    def query(source: Source, pkey: Optional[int], path: Path) -> Iterable[Record]:
        query = f'SELECT {",".join(Record._fields)} FROM "{source}.com"'
        if pkey is not None:
            query += f" WHERE id={pkey}"
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            return map(lambda t: Record(*t), cursor.execute(query).fetchall())

    @staticmethod
    def fetch(record: Record, timeout: float) -> str:
        with Client(headers=HEADERS, timeout=timeout) as client:
            resp = client.get(record.url)
            assert resp.is_success, (
                f"Failed to fetch content from {record.url}, status_code={resp.status_code}, text={resp.text}"
            )
            return resp.content.decode()

    @staticmethod
    async def afetch(*records: Record, timeout: float, limit: int):
        def batch_iter[T](data: Sequence[T]):
            length = len(data)
            for i in range(0, length, limit):
                yield data[i : i + limit]

        limits = Limits(max_connections=limit, max_keepalive_connections=1)
        async with AsyncClient(headers=HEADERS, timeout=timeout, limits=limits) as c:

            async def fetch(record: Record) -> str:
                r = await c.get(record.url)
                assert r.is_success, f"Failed to fetch {record.title} from {record.url}"
                return r.content.decode()

            for batch in batch_iter(records):
                tasks = map(fetch, batch)
                pages = await asyncio.gather(*tasks, return_exceptions=True)
                for page in pages:
                    yield page

    @staticmethod
    def html_handler(source: Source) -> Callable[[str], str]:
        if source == "cppreference":
            from cppref.core.cppreference import process

            return process
        raise NotImplementedError(f"{source} is not supported for now.")

    @staticmethod
    def read_file(path: Path) -> str:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    @staticmethod
    def write_file(path: Path, content: str):
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)


class Configuration:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._dirty = False
        self._conf: dict[ConfKey, Any] = dict()

    @staticmethod
    def _from_scratch() -> dict[ConfKey, Any]:
        ret: dict[ConfKey, Any] = dict()
        ret["source"] = "cppreference"
        ret["db_path"] = str(
            Path(os.getenv("XDG_DATA_HOME") or "~/.local/state")
            .joinpath("cppref")
            .joinpath("index.db")
            .expanduser()
            .absolute()
        )
        return ret

    @overload
    def __setitem__(self, key: Literal["source"], value: Source) -> None: ...

    @overload
    def __setitem__(self, key: Literal["db_path"], value: str) -> None: ...

    @overload
    def __getitem__(self, key: Literal["source"]) -> Source: ...

    @overload
    def __getitem__(self, key: Literal["db_path"]) -> str: ...

    def __enter__(self):
        if not self._path.exists():
            self._conf = Configuration._from_scratch()
            self._dirty = True
        else:
            with open(self._path, "r", encoding="utf-8") as file:
                self._conf = cast(dict[ConfKey, Any], toml.load(file))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._dirty:
            return False
        with open(self._path, "w", encoding="utf-8") as file:
            toml.dump(cast(dict[str, Any], self._conf), file)
        return False

    def __setitem__(self, key: ConfKey, value: ConfVal):
        self._dirty = True
        self._conf[key] = value

    def __getitem__(self, key: ConfKey) -> ConfVal:
        return self._conf[key]
