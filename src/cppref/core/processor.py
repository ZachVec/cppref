from __future__ import annotations

from copy import deepcopy
from typing import Callable, Dict, Optional, Concatenate
from lxml.html import HtmlElement

type Matcher = Callable[[HtmlElement], bool]
type Handler[**P, R] = Callable[Concatenate[HtmlElement, P], R]


class Processor[**P, R]:
    def __init__(self) -> None:
        self._routes: Dict[Matcher, Handler[P, R]] = {}
        self._default: Optional[Handler[P, R]] = None

    def route(self, matcher: Optional[Matcher] = None):
        def decorator(fn: Handler[P, R]) -> Handler[P, R]:
            if matcher is None:
                assert self._default is None, "Duplicate default processor"
                self._default = fn
            else:
                self._routes[matcher] = fn
            return fn

        return decorator

    def process(self, element: HtmlElement, *args: P.args, **kwargs: P.kwargs) -> R:
        for matcher, handler in self._routes.items():
            if matcher(element):
                return handler(element, *args, **kwargs)
        assert self._default is not None, (
            f"No fallback for element: tag={element.tag}, class={element.get('class')}"
        )
        return self._default(element, *args, **kwargs)

    def clone(self) -> Processor[P, R]:
        ret = Processor()
        ret._routes = deepcopy(self._routes)
        ret._default = deepcopy(self._default)
        return ret
