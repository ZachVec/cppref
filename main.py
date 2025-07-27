import asyncio
import sys
from pathlib import Path

import httpx

from cppref import DBManager, cpprefence_processor, download

ROOT = Path(".").absolute()


def test_parser(filename: Path, url: str):
    if ROOT.joinpath(filename).exists():
        with open(filename, "r", encoding="utf-8") as file:
            text = file.read()
    else:
        text = httpx.get(url).content.decode()
        with open(filename, "w", encoding="utf-8") as file:
            file.write(text)
    try:
        document = cpprefence_processor(text)
    except Exception as e:
        print(str(e))
    else:
        with open("output.man", "w", encoding="utf-8") as file:
            file.write(document)


async def download_htmls(dbpath: Path, save_path: Path, batch_size: int = 30):
    manager = DBManager(dbpath)
    datas = manager.get_url("cppreference")
    fetch = [(f"{pkey}", url) for pkey, _, url in datas]
    metas = {f"{pkey}": title for pkey, title, _ in datas}
    for pkey, _, e in await download(save_path, *fetch, batch_size=batch_size):
        print(f"({pkey}, {metas[pkey]}, {str(e)})", file=sys.stderr)


if __name__ == "__main__":
    # 26 array
    # 35 vector
    # 1249 vector::push_back
    DB_PATH = ROOT.joinpath("resources", "index.db").absolute()
    CPPREFERENCE = ROOT.joinpath("resources", "cppreference")
    # NOTE: Download all htmls
    # asyncio.run(download_htmls(DB_PATH, CPPREFERENCE))
    mappings = {
        "array": (
            CPPREFERENCE.joinpath("26.html"),
            "https://en.cppreference.com/w/cpp/container/array.html",
        ),
        "vector": (
            CPPREFERENCE.joinpath("35.html"),
            "https://en.cppreference.com/w/cpp/container/vector.html",
        ),
        "vector_push_back": (
            CPPREFERENCE.joinpath("1249.html"),
            "https://en.cppreference.com/w/cpp/container/vector/push_back.html",
        ),
    }
