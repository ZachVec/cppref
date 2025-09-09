from collections import deque
from typing import override

from lxml.html import HtmlElement

from cppref.core.cppreference.table.base import Table
from cppref.core.cppreference.table.typing_ import RowSpec, RowText, TabInfo
from cppref.core.cppreference.table.width import table_width
from cppref.core.processor import Processor


class TParBegin(Table):
    @override
    def nested(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        specs, texts = list[RowSpec](), list[RowText]()

        for row in self._table:
            if (ncols := len(row)) == 1:
                specs.append(deque[str](["lt", *["s" for _ in range(width - 1)]]))
                texts.append(deque[str]([Table.text(row)]))
                continue
            assert ncols == 3, f"t-par-begin unexpected {ncols=}"
            specs.append(deque[str](["rt"]))
            texts.append(deque[str]([Table.text(row[0])]))
            spec, text = Table.td(row[2], width - 1, "l", p)
            it = zip(spec, text, strict=True)
            spec, text = next(it)
            specs[-1].extend(spec)
            texts[-1].extend(text)
            for spec, text in it:
                specs.append(deque[str](["^", *spec]))
                texts.append(deque[str](["", *text]))

        return specs, texts

    @override
    def normal(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        specs, texts = list[RowSpec](), list[RowText]()
        for row in self._table:
            specs.append(deque[str](["-" for _ in range(width)]))
            if (ncols := len(row)) == 1:
                specs.append(deque[str](["lt", *["s" for _ in range(width - 1)]]))
                texts.append(deque[str]([Table.text(row)]))
                continue
            assert ncols == 3, f"t-par-begin unexpected {ncols=}"
            specs.append(deque[str](["rt"]))
            texts.append(deque[str]([Table.text(row[0])]))
            spec, text = Table.td(row[2], width - 1, "lx", p)
            it = zip(spec, text, strict=True)
            spec, text = next(it)
            specs[-1].extend(spec)
            texts[-1].extend(text)
            for spec, text in it:
                specs.append(deque[str](["^", *spec]))
                texts.append(deque[str](["", *text]))
        return specs[1:], texts

    @staticmethod
    def process(table: HtmlElement, p: Processor[[int], TabInfo]) -> str:
        texts = list[str]()
        texts.append(".TS")
        texts.append("box expand tab(;);")
        texts.append(Table.to_table(TParBegin(table).normal(table_width(table), p)))
        texts.append(".TE")
        # texts.append(".sp")
        return "\n".join(texts)
