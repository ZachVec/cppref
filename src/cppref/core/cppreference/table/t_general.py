from collections import deque
from typing import Optional, override

from lxml.html import HtmlElement

from cppref.core.cppreference.table.base import Table
from cppref.core.cppreference.table.typing_ import RowSpec, RowText, TabInfo
from cppref.core.cppreference.table.width import table_width
from cppref.core.processor import Processor


class GeneralTable(Table):
    def bold(self, element: HtmlElement) -> bool:
        return element.tag == "th"

    def extend(self, index: int, total: int) -> bool:
        return False

    @override
    def nested(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        ncols = sum([int(cell.get("colspan", "1")) for cell in self._table[0]])
        assert width == ncols, f"Expect {ncols} == {width}"
        specs, texts, spans = list[RowSpec](), list[RowText](), [0] * ncols

        title: Optional[str] = None
        for caption in self._table.iterchildren("caption"):
            assert title is None, "Duplicate title for table"
            title = Table.text(caption)
            caption.drop_tree()

        if title is not None:
            specs.append(deque[str](["cb", *["s" for _ in range(ncols - 1)]]))
            texts.append(deque[str](title))

        for row in self._table:
            col_index = 0
            spec, text = deque[str](), deque[str]()
            for col in row:
                while spans[col_index] > 0:
                    spans[col_index] -= 1
                    col_index += 1
                    spec.append("^")
                    text.append("")
                assert col_index < ncols
                rowspan = int(col.get("rowspan", "1"))
                colspan = int(col.get("colspan", "1"))
                spans[col_index] = rowspan - 1
                bold = "b" if self.bold(col) else ""
                spec.append(f"c{bold}")
                spec.extend(["s" for _ in range(colspan - 1)])
                text.append(Table.text(col))
                col_index += colspan
            while col_index < ncols:
                if spans[col_index] > 0:
                    spans[col_index] -= 1
                    spec.append("^")
                else:
                    spec.append("c")
                text.append("")
                col_index += 1
            specs.append(spec)
            texts.append(text)

        return specs, texts

    @override
    def normal(self, width: int, p: Processor[[int], TabInfo]) -> TabInfo:
        ncols = sum([int(cell.get("colspan", "1")) for cell in next(self._table.iterchildren("tr"))])  # fmt: off
        assert width == ncols, f"Expect {ncols} == {width}"
        specs, texts, spans = list[RowSpec](), list[RowText](), [0] * ncols

        title: Optional[str] = None
        for caption in self._table.iterchildren("caption"):
            assert title is None, "Duplicate title for table"
            title = Table.text(caption)
            caption.drop_tree()

        if title is not None:
            specs.append(deque[str](["cb", *["s" for _ in range(ncols - 1)]]))
            texts.append(deque[str]([title]))

        for row in self._table:
            col_index = 0
            spec, text = deque[str](), deque[str]()
            for col in row:
                while spans[col_index] > 0:
                    spans[col_index] -= 1
                    col_index += 1
                    spec.append("^")
                    text.append("")
                assert col_index < ncols
                rowspan = int(col.get("rowspan", "1"))
                colspan = int(col.get("colspan", "1"))
                spans[col_index] = rowspan - 1
                bold = "b" if self.bold(col) else ""
                extend = "x" if self.extend(col_index, ncols) else ""
                spec.append(f"c{bold}{extend}")
                spec.extend(["s" for _ in range(colspan - 1)])
                text.append(Table.text(col))
                col_index += colspan
            while col_index < ncols:
                if spans[col_index] > 0:
                    spans[col_index] -= 1
                    spec.append("^")
                else:
                    spec.append("c")
                text.append("")
                col_index += 1
            specs.append(spec)
            texts.append(text)

        return specs, texts

    @classmethod
    def process(cls, table: HtmlElement, p: Processor[[int], TabInfo]):
        width = table_width(table)
        if width > 10:
            return ".I there should be a table, but its crowded."
        texts: list[str] = list()
        texts.append(".TS")
        texts.append("allbox expand tab(;);")
        texts.append(Table.to_table(cls(table).normal(width, p)))
        texts.append(".TE")
        texts.append(".sp")
        return "\n".join(texts)


class WikiTable(GeneralTable):
    @override
    def extend(self, index: int, total: int) -> bool:
        return total == 3 and index == 1 or total < 5 and index == total - 1


class DscTable(GeneralTable):
    @override
    def extend(self, index: int, total: int) -> bool:
        if total == 3 or total == 4:
            return index == total - 2
        if total < 5:
            return index == total - 1
        return False
