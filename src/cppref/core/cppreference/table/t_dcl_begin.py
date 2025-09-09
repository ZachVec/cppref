from collections import deque
from typing import override

from lxml.html import HtmlElement

from cppref.core.cppreference.table.width import table_width
from cppref.core.cppreference.table.base import Table
from cppref.core.cppreference.table.typing_ import RowSpec, RowText, TabInfo
from cppref.core.processor import Processor


class TDclBegin(Table):
    @override
    def nested(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        specs, texts = list[RowSpec](), list[RowText]()
        for row in self._table:
            spec, text = Table.td(row[0], width - 1, "l", p)
            specs.extend(spec)
            texts.extend(text)
            it = zip(spec, text, strict=True)
            spec, text = next(it)

            if (length := len(row)) == 1:
                spec.append("s")
            elif length == 2:
                spec.append("c")
                text.append(Table.text(row[1]))
            elif length == 3:
                spec.append("c")
                text.extend(" ".join(map(Table.text, [row[1], row[2]])))
            else:
                assert False, f"t-dcl-begin unexpected {length=}"

            for spec, text in it:
                spec.append("^")
                text.append("")
        return specs, texts

    @override
    def normal(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        specs, texts = list[RowSpec](), list[RowText]()
        for row in self._table:
            specs.append(deque[str](["-" for _ in range(width)]))
            spec, text = Table.td(row[0], width - 2, "lx", p)
            specs.extend(spec)
            texts.extend(text)
            it = zip(spec, text, strict=True)
            spec, text = next(it)

            if (length := len(row)) == 1:
                spec.extend(["s", "s"])
            elif length == 2:
                spec.extend(["c", "s"])
                text.extend([Table.text(row[1])])
            elif length == 3:
                spec.extend(["c", "c"])
                text.extend(map(Table.text, [row[1], row[2]]))
            else:
                assert False, f"t-dcl-begin unexpected {length=}"

            for spec, text in it:
                spec.extend(["^", "^"])
                text.extend(["", ""])

        # append seperate line
        specs.append(deque[str](["-" for _ in range(width)]))
        specs.append(deque[str](["l" for _ in range(width)]))
        texts.append(deque[str](["" for _ in range(width)]))

        return specs, texts

    @staticmethod
    def process(table: HtmlElement, p: Processor[[int], TabInfo]) -> str:
        texts = list[str]()
        # texts.append('.SH "SYNOPSIS"')
        texts.append(".TS")
        texts.append("expand tab(;);")
        texts.append(Table.to_table(TDclBegin(table).normal(table_width(table), p)))
        texts.append(".TE")
        texts.append(".sp")
        texts.append('.SH "DESCRIPTION"')
        return "\n".join(texts)
