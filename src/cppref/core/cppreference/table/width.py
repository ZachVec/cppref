from dataclasses import dataclass

from lxml.html import HtmlElement

from cppref.core.processor import Processor


@dataclass
class TableMeta:
    index: int  # index of which column may contain nested tables
    ncols: int  # only the rows with this many columns will be considered as may contain nested tables
    nested: int  # render as nested ncols if table is nested
    normal: int  # render as nested ncols if table is not nested


_t_dcl_begin = TableMeta(0, 3, 2, 3)
_t_par_begin = TableMeta(2, 3, 2, 2)
_t_dsc_begin = TableMeta(1, 2, 2, 3)
_t_rev_begin = TableMeta(0, 2, 2, 2)
_t_sdsc_begin = TableMeta(0, 3, 2, 2)
_nested = Processor[[], int]()
normal = Processor[[], int]()


def _default(table: HtmlElement) -> int:
    row0 = next(table.iterchildren("tr"))
    return sum([int(cell.get("colspan", "1")) for cell in row0])


def _width(meta: TableMeta, is_nested: bool):
    def td_width(td: HtmlElement):
        tables = list(td.iterchildren("table"))
        return 1 if len(tables) == 0 else max(map(_nested.process, tables))

    extra = meta.nested if is_nested else meta.normal

    def fn(table: HtmlElement) -> int:
        rows = list(filter(lambda r: len(r) == meta.ncols, table))
        ret = extra if len(rows) == 0 else max(map(lambda r: td_width(r[meta.index]), rows)) + extra - 1  # fmt: off
        return ret

    return fn


_nested.route()(_default)
_nested.route(lambda e: "t-dcl-begin" in e.get("class", ""))(_width(_t_dcl_begin, True))
_nested.route(lambda e: "t-dsc-begin" in e.get("class", ""))(_width(_t_dsc_begin, True))
_nested.route(lambda e: "t-rev-begin" in e.get("class", ""))(_width(_t_rev_begin, True))
_nested.route(lambda e: "t-par-begin" in e.get("class", ""))(_width(_t_par_begin, True))
_nested.route(lambda e: "t-sdsc-begin" in e.get("class", ""))(_width(_t_sdsc_begin, True))  # fmt: off

normal.route()(_default)
normal.route(lambda e: "t-dcl-begin" in e.get("class", ""))(_width(_t_dcl_begin, False))
normal.route(lambda e: "t-dsc-begin" in e.get("class", ""))(_width(_t_dsc_begin, False))
normal.route(lambda e: "t-rev-begin" in e.get("class", ""))(_width(_t_rev_begin, False))
normal.route(lambda e: "t-par-begin" in e.get("class", ""))(_width(_t_par_begin, False))
normal.route(lambda e: "t-sdsc-begin" in e.get("class", ""))(_width(_t_sdsc_begin, False))  # fmt: off


def table_width(table: HtmlElement):
    return normal.process(table)
