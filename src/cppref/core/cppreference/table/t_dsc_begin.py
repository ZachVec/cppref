from collections import deque
from typing import override

from lxml.html import HtmlElement

from cppref.core.cppreference.table.base import Table
from cppref.core.cppreference.table.typing_ import RowSpec, RowText, TabInfo
from cppref.core.cppreference.table.width import table_width
from cppref.core.processor import Processor


class TDscBegin(Table):
    @override
    def nested(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        specs, texts = list[RowSpec](), list[RowText]()
        for row in self._table:
            if (ncols := len(row)) == 1:
                specs.append(deque[str](["cbd", *["s" for _ in range(width - 1)]]))
                texts.append(deque[str]([Table.text(row)]))
                continue
            assert ncols == 2, f"t-dsc-begin unexpected {ncols=}"
            spec, text = TDscBegin.nested_column1(row[0])
            specs.append(deque[str]([spec]))
            texts.append(deque[str]([text]))

            spec, text = Table.td(row[1], width - 1, "l", p)
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
        specs, texts, ncols = list[RowSpec](), list[RowText](), None
        for row in self._table:
            prev_ncols = ncols
            if (ncols := len(row)) == 1:
                if isinstance(prev_ncols, int) and prev_ncols == 1:
                    specs.append(deque[str](["-", "-", *["-" for _ in range(width - 2)]]))  # fmt: off
                else:
                    specs.append(deque[str](["-", "-", "|", *["-" for _ in range(width - 2)]]))  # fmt: off
                specs.append(deque[str](["lbd", "s", *["s" for _ in range(width - 2)]]))
                texts.append(deque[str]([Table.text(row)]))
                specs.append(deque[str](["^", "s", *["s" for _ in range(width - 2)]]))
                texts.append(deque[str]([""]))
                continue
            specs.append(deque[str](["-", "-", "|", *["-" for _ in range(width - 2)]]))
            assert ncols == 2, f"t-dsc-begin unexpected {ncols=}"
            spec, text = TDscBegin.column1(row[0])
            specs.append(spec)
            texts.append(text)
            spec, text = Table.td(row[1], width - 2, "lx", p)
            it = zip(spec, text, strict=True)
            spec, text = next(it)
            specs[-1].extend(["|", *spec])
            texts[-1].extend(text)
            for spec, text in it:
                specs.append(deque[str](["^", "^", "|", *["-" for _ in range(width - 2)]]))  # fmt: off
                texts.append(deque[str](["", ""]))
                specs.append(deque[str](["^", "^", "|", *spec]))
                texts.append(deque[str](["", "", *text]))

        return specs[1:], texts

    @staticmethod
    def nested_column1(td: HtmlElement) -> tuple[str, str]:
        tlines = td.find_class("t-lines")
        if (ntlines := len(tlines)) == 0:
            return "l", Table.text(td)

        if ntlines == 1:
            texts = [s.text_content().strip() for s in tlines[0]]
            return "l", "\n.br\n".join(texts)

        assert (ntlines := len(tlines)) == 2, f"unexpected {ntlines=}"

        col1 = [s.text_content().strip() for s in tlines[0]]
        pad1 = "".join([" " for _ in range(max(map(len, col1)))])
        col2 = [s.text_content().strip() for s in tlines[1]]
        pad2 = "".join([" " for _ in range(max(map(len, col1)))])
        diff = len(col1) - len(col2)
        col1.extend([pad1 for _ in range(-diff)])
        col2.extend([pad2 for _ in range(diff)])
        return "l", "\n.br\n".join(map(" ".join, zip(col1, col2, strict=True)))

    @staticmethod
    def column1(td: HtmlElement) -> tuple[RowSpec, RowText]:
        tlines = td.find_class("t-lines")
        if (ntlines := len(tlines)) == 0:
            return deque[str](["l", "s"]), deque[str]([Table.text(td)])

        if ntlines == 1:
            texts = [s.text_content().strip() for s in tlines[0]]
            return deque[str](["l", "s"]), deque[str](["\n.br\n".join(texts)])

        if ntlines == 2:
            texts = list[list[str]]()
            texts.append([s.text_content().strip() for s in tlines[0]])
            texts.append([s.text_content().strip() for s in tlines[1]])
            return deque[str](["l", "l"]), deque[str](map("\n.br\n".join, texts))

        assert False, f"Unexpected len(tlines)={ntlines}"

    @staticmethod
    def process(table: HtmlElement, p: Processor[[int], TabInfo]) -> str:
        texts = list[str]()
        texts.append(".TS")
        texts.append("box expand tab(;);")
        texts.append(Table.to_table(TDscBegin(table).normal(table_width(table), p)))
        texts.append(".TE")
        return "\n".join(texts)
