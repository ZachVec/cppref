from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Callable, Sequence

from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

from cppref.typing_ import Record, Source


class Utils:
    @staticmethod
    def query(source: Source, path: Path) -> list[Record]:
        assert path.exists() and path.is_file(), f"{path} does not exists!"
        query = f'SELECT {",".join(Record._fields)} FROM "{source}.com"'
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()
            ret = list(map(lambda t: Record(*t), cursor.execute(query).fetchall()))
        conn.close()
        return ret

    @staticmethod
    def fetch(record: Record, timeout: float) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            resp = page.goto(record.url, timeout=timeout, wait_until="networkidle")
            assert resp is not None, f"Timeout: {record}"
            assert resp.ok, f"Request failed: status={resp.status_text}, {record}"
            content = page.content()
            page.close()
            browser.close()
            return content

    @staticmethod
    async def afetch(*records: Record, timeout: float, limit: int):
        def batch_iter[T](data: Sequence[T]):
            length = len(data)
            for i in range(0, length, limit):
                yield data[i : i + limit]

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            pages = [await browser.new_page() for _ in range(limit)]

            async def _fetch(index: int, record: Record) -> str:
                resp = await pages[index].goto(record.url, timeout=timeout, wait_until="networkidle")  # fmt: off
                assert resp is not None, f"Timeout: {record}"
                assert resp.ok, f"Request failed: status={resp.status_text}, {record}"
                return await pages[index].content()

            for batch in batch_iter(records):
                tasks = map(lambda t: _fetch(t[0], t[1]), enumerate(batch))
                htmls = await asyncio.gather(*tasks, return_exceptions=True)
                for html in htmls:
                    yield html

            for page in pages:
                await page.close()

            await browser.close()

    @staticmethod
    def html_handler(source: Source) -> Callable[[str, str], str]:
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
