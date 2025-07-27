from typing import Callable

from lxml.html import HtmlElement


class Processor:
    def __init__(self):
        self._handlers: dict[str, Callable[[HtmlElement], str]] = dict()

    def route(self, tag: str):
        def decorator(fn: Callable[[HtmlElement], str]) -> Callable[[HtmlElement], str]:
            self._handlers[tag] = fn
            return fn

        return decorator

    def process(self, tree: HtmlElement) -> str:
        handler = self._handlers.get(str(tree.tag))
        assert handler is not None, f"handler for {tree.tag} is not registered"
        return handler(tree)
