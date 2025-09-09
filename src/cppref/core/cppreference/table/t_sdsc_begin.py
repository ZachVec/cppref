from collections import deque
from typing import override

from lxml.html import HtmlElement

from cppref.core.cppreference.table.base import Table
from cppref.core.cppreference.table.typing_ import RowSpec, RowText, TabInfo
from cppref.core.cppreference.table.width import table_width
from cppref.core.processor import Processor


class TSdscBegin(Table):
    @override
    def nested(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        specs, texts = list[RowSpec](), list[RowText]()
        for row in self._table:
            assert (ncols := len(row)) == 3, f"t-sdsc-begin unexpected {ncols=}"
            spec, text = Table.td(row[0], width - 1, "l", p)
            specs.extend(spec)
            texts.extend(text)
            it = zip(spec, text, strict=True)
            spec, text = next(it)
            spec.append("c")
            text.append(" ".join(map(Table.text, [row[1], row[2]])))
            for spec, text in it:
                spec.append("^")
                text.append("")
        return specs, texts

    @override
    def normal(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        specs, texts = list[RowSpec](), list[RowText]()
        for row in self._table:
            assert (ncols := len(row)) == 3, f"t-sdsc-begin unexpected {ncols=}"
            specs.append(deque[str](["-" for _ in range(width)]))
            spec, text = Table.td(row[0], width - 1, "lx", p)
            specs.extend(spec)
            texts.extend(text)
            it = zip(spec, text, strict=True)
            spec, text = next(it)
            spec.append("c")
            text.append(" ".join(map(Table.text, [row[1], row[2]])))
            for spec, text in it:
                spec.append("^")
                text.append("")
        return specs[1:], texts

    @staticmethod
    def process(table: HtmlElement, p: Processor[[int], TabInfo]) -> str:
        texts = list[str]()
        texts.append(".TS")
        texts.append("box expand tab(;);")
        texts.append(Table.to_table(TSdscBegin(table).normal(table_width(table), p)))
        texts.append(".TE")
        texts.append(".sp")
        return "\n".join(texts)
