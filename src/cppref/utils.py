from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Callable, Sequence

from httpx import AsyncClient, Client, Headers, Limits

from cppref.typing_ import Record, Source

HDRS = Headers()
HDRS.setdefault(
    "User-Agent",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0",
)


class Utils:
    @staticmethod
    def query(source: Source, path: Path) -> list[Record]:
        assert path.exists() and path.is_file(), f"{path} does not exists!"
        query = f'SELECT {",".join(Record._fields)} FROM "{source}.com"'
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            return list(map(lambda t: Record(*t), cursor.execute(query).fetchall()))

    @staticmethod
    def fetch(record: Record, timeout: float) -> str:
        with Client(headers=HDRS, timeout=timeout, follow_redirects=True) as client:
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
        async with AsyncClient(headers=HDRS, timeout=timeout, limits=limits, follow_redirects=True) as c:  # fmt: off

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
