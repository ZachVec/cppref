from __future__ import annotations

from subprocess import PIPE, Popen
from typing import Any


class FzfContext:
    def __init__(self, *args: str, **kwargs: str) -> None:
        arguments = list(args)
        arguments.extend(map(lambda kv: f"{kv[0]}={kv[1]}", kwargs.items()))
        cmd = f"fzf {' '.join(arguments)}"
        self._process = Popen(cmd, stdin=PIPE, stdout=PIPE, text=True, shell=True)

    def __enter__(self) -> FzfContext:
        return self

    def __exit__(self, __1__, __2__, __3__):
        assert self._process.stdin is not None
        self._process.stdin.close()
        assert self._process.stdout is not None
        self._process.stdout.close()

    def add_option(self, *options: Any):
        if self._process.poll() is not None:
            return False
        print("\n".join(map(str, options)), file=self._process.stdin, flush=True)
        return True

    def get_selection(self) -> list[str]:
        assert self._process.stdout is not None
        self._process.wait()
        return self._process.stdout.read().splitlines()
