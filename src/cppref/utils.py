from __future__ import annotations

import asyncio
import gzip
import sqlite3
from asyncio import Queue
from pathlib import Path
from typing import Callable

from playwright.async_api import Page, async_playwright
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
    async def afetch(
        *records: Record,
        timeout: float,
        limit: int,
        on_success: Callable[[Record, str], None],
        on_failed: Callable[[Record, Exception], None],
    ):
        _records = Queue[Record]()
        for recrod in records:
            _records.put_nowait(recrod)

        _results = Queue[tuple[Record, Exception | str]]()

        async def producer(page: Page):
            while not _records.empty():
                record = _records.get_nowait()
                try:
                    resp = await page.goto(record.url, timeout=timeout, wait_until="networkidle")  # fmt: off
                    assert resp is not None, f"Timeout: {record}"
                    assert resp.ok, f"Request failed: {record}, status={resp.status_text}"  # fmt: off
                except Exception as e:
                    _results.put_nowait((record, e))
                else:
                    _results.put_nowait((record, await page.content()))
                finally:
                    _records.task_done()

        async def customer():
            while True:
                record, resp = await _results.get()
                if isinstance(resp, str):
                    try:
                        on_success(record, resp)
                    except Exception as e:
                        on_failed(record, e)
                else:
                    on_failed(record, resp)
                _results.task_done()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            pages = [await browser.new_page() for _ in range(limit)]
            producers = [asyncio.create_task(producer(pages[i])) for i in range(limit)]
            customers = [asyncio.create_task(customer()) for _ in range(limit)]
            await _records.join()
            for p in producers:
                p.cancel()
            await _results.join()
            for c in customers:
                c.cancel()

            await asyncio.gather(*producers, return_exceptions=True)
            await asyncio.gather(*customers, return_exceptions=True)

            for page in pages:
                await page.close()

            await browser.close()

    @staticmethod
    def html_handler(source: Source) -> Callable[[str, Record], str]:
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

    @staticmethod
    def write_man3(path: Path, content: str):
        with gzip.open(path, "w") as file:
            file.write(content.encode("utf-8"))
