import asyncio
from pathlib import Path

import httpx


async def download(
    directory: Path,
    *urls: tuple[str, str],
    timeout: float = 10,
    max_connections: int = 10,
    batch_size: int = 10,
):
    """Save the urls as html

    Args:
        directory: Directory to save.
        urls: (basename, url) pairs.
        timeout: timeout in seconds for each request.
        max_connections: max_connections in a batch.
        batch_size: number of requests in each batch.
    """
    if not directory.exists():
        directory.mkdir(parents=True)

    async def make_task(client: httpx.AsyncClient, pkey: str, url: str):
        resp = await client.get(url)
        assert resp.is_success, f"status_code={resp.status_code}"
        with open(directory.joinpath(f"{pkey}.html"), "w", encoding="utf-8") as file:
            file.write(resp.content.decode())

    headers = httpx.Headers()
    headers.setdefault(
        "User-Agent",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/111.0",
    )

    length = len(urls)
    fails: list[tuple[str, str, BaseException]] = list()
    async with httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(timeout=timeout),
        follow_redirects=True,
        limits=httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=1,
        ),
    ) as c:
        for i in range(0, length, batch_size):
            tasks = map(lambda t: make_task(c, t[0], t[1]), urls[i : i + batch_size])
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for j, res in enumerate(results):
                if res is None:
                    continue
                fails.append((*urls[i + j], res))

    return fails


if __name__ == "__main__":
    dir = Path("resources/cppreference").absolute()
    urls = [
        ("10", "https://en.cppreference.com/w/cpp/atomic/memory_order"),
        ("11", "https://en.cppreference.com/w/cpp/algorithm"),
    ]

    ret = asyncio.run(download(dir, *urls))
    for pkey, url, ex in ret:
        print(f'("{pkey}", "{url}"), {str(ex)}')
