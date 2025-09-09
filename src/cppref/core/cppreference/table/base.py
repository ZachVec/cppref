import re
from collections import deque

from lxml.html import HtmlElement

from cppref.core.cppreference.table.typing_ import RowSpec, RowText, TabInfo
from cppref.core.processor import Processor


class Table:
    def __init__(self, table: HtmlElement) -> None:
        self._table = table

    @staticmethod
    def text(e: HtmlElement):
        return re.sub(r"\n+", "\n.br\n", e.text_content().strip())

    @staticmethod
    def to_table(info: TabInfo) -> str:
        specs, texts = info
        specs = "\n".join(map(" ".join, specs))
        texts = map(lambda r: map(lambda t: f"T{{\n{t}\nT}}", r), texts)
        texts = "\n".join(map(";".join, texts))
        return f"{specs}.\n{texts}"

    @staticmethod
    def td(td: HtmlElement, width: int, default: str, p: Processor[[int], TabInfo]):
        specs, texts = list[RowSpec](), list[RowText]()
        nested_tables = list(td.iterchildren("table"))
        if len(nested_tables) == 0:
            spec = deque[str]([default, *["s" for _ in range(width - 1)]])
            text = deque[str]([Table.text(td)])
            specs.append(spec)
            texts.append(text)
            return specs, texts

        hanging = list[str]()
        if td.text is not None and len(td.text.strip()) > 0:
            hanging.append(td.text)
        for element in td:
            if element.tag != "table":
                hanging.append(element.text_content())
            else:
                hanging = "".join(hanging).strip()
                if len(hanging) > 0:
                    spec, text = deque[str](), deque[str]()
                    spec.append(default)
                    text.append(re.sub(r"\n+", "\n.br\n", hanging))
                    spec.extend(["s" for _ in range(width - 1)])
                    specs.append(spec)
                    texts.append(text)
                hanging = list[str]()
                spec, text = p.process(element, width)
                specs.extend(spec)
                texts.extend(text)
            if element.tail is not None:
                hanging.append(element.tail)
        hanging = "".join(hanging).strip()
        if len(hanging) > 0:
            spec, text = deque[str](), deque[str]()
            spec.append(default)
            text.append(re.sub(r"\n+", "\n.br\n", hanging))
            spec.extend(["s" for _ in range(width - 1)])
            specs.append(spec)
            texts.append(text)

        return specs, texts

    def nested(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        return NotImplemented

    def normal(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        return NotImplemented
