from lxml.etree import strip_tags
from lxml.html import HtmlElement
from cppref.core.cppreference.table.t_dcl_begin import TDclBegin
from cppref.core.cppreference.table.t_dsc_begin import TDscBegin
from cppref.core.cppreference.table.t_general import DscTable, GeneralTable, WikiTable
from cppref.core.cppreference.table.t_par_begin import TParBegin
from cppref.core.cppreference.table.t_rev_begin import TRevBegin
from cppref.core.cppreference.table.t_sdsc_begin import TSdscBegin
from cppref.core.cppreference.table.typing_ import TabInfo
from cppref.core.processor import Processor


_tabinfo = Processor[[int], TabInfo]()


@_tabinfo.route()
def _(table: HtmlElement, width: int) -> TabInfo:
    return GeneralTable(table).nested(width, _tabinfo)


@_tabinfo.route(lambda e: "dsctable" in e.get("class", ""))
def _(table: HtmlElement, width: int) -> TabInfo:
    return DscTable(table).nested(width, _tabinfo)


@_tabinfo.route(lambda e: "wikitable" in e.get("class", ""))
def _(table: HtmlElement, width: int) -> TabInfo:
    return WikiTable(table).nested(width, _tabinfo)


@_tabinfo.route(lambda e: "t-dcl-begin" in e.get("class", ""))
def _(table: HtmlElement, width: int) -> TabInfo:
    for element in table.find_class("t-dcl-sep"):
        element.drop_tree()
    return TDclBegin(table).nested(width, _tabinfo)


@_tabinfo.route(lambda e: "t-dsc-begin" in e.get("class", ""))
def _(table: HtmlElement, width: int) -> TabInfo:
    return TDscBegin(table).nested(width, _tabinfo)


@_tabinfo.route(lambda e: "t-par-begin" in e.get("class", ""))
def _(table: HtmlElement, width: int) -> TabInfo:
    return TParBegin(table).nested(width, _tabinfo)


@_tabinfo.route(lambda e: "t-rev-begin" in e.get("class", ""))
def _(table: HtmlElement, width: int) -> TabInfo:
    return TRevBegin(table).nested(width, _tabinfo)


@_tabinfo.route(lambda e: "t-sdsc-begin" in e.get("class", ""))
def _(table: HtmlElement, width: int) -> TabInfo:
    for td in table.find_class("t-sdsc-sep"):
        parent = td.getparent()
        assert parent is not None, "Panic"
        parent.drop_tree()
    return TSdscBegin(table).nested(width, _tabinfo)


_table = Processor[[], str]()


@_table.route()
def _(table: HtmlElement) -> str:
    return GeneralTable.process(table, _tabinfo)


@_table.route(lambda e: "dsctable" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    return DscTable.process(table, _tabinfo)


@_table.route(lambda e: "wikitable" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    return WikiTable.process(table, _tabinfo)


@_table.route(lambda e: "t-dcl-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    for element in table.find_class("t-dcl-sep"):
        element.drop_tree()
    return TDclBegin.process(table, _tabinfo)


@_table.route(lambda e: "t-dsc-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    return TDscBegin.process(table, _tabinfo)


@_table.route(lambda e: "t-par-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    return TParBegin.process(table, _tabinfo)


@_table.route(lambda e: "t-rev-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    return TRevBegin.process(table, _tabinfo)


@_table.route(lambda e: "t-sdsc-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    for td in table.find_class("t-sdsc-sep"):
        parent = td.getparent()
        assert parent is not None, "Panic"
        parent.drop_tree()
    return TSdscBegin.process(table, _tabinfo)


def table(table: HtmlElement) -> str:
    strip_tags(table, "tbody")
    if len(table.text_content().strip()) == 0:
        return ""
    if "mw-collapsible" in table.get("class", ""):
        return "\n.I there should be a table, but its crowded.\n"
    if "mw-collapsed" in table.get("class", ""):
        return "\n.I there should be a table, but its crowded.\n"
    return f"\n{_table.process(table)}\n"


__all__ = ["table"]
