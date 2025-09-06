from typing import Callable
from lxml.etree import strip_tags
from lxml.html import HtmlElement

from cppref.core.processor import Processor


def collect(elem: HtmlElement, processor: Processor[[], str]) -> str:
    texts: list[str] = list()
    if elem.text is not None and len(elem.text.strip()) > 0:
        texts.append(elem.text)

    for element in elem:
        texts.append(processor.process(element))
        if element.tail is not None and len(element.tail.strip()) > 0:
            texts.append(element.tail)

    return "".join(texts)


def nested_table_processor(
    table: HtmlElement,
    formatter: Callable[[HtmlElement], str],
    texter: Callable[[HtmlElement], list[str]],
) -> tuple[list[str], list[list[str]]]:
    assert table.tag == "table", f"Expect table, but got {table.tag}"
    strip_tags(table, "tbody")
    formats, texts = list[str](), list[list[str]]()
    for row in table:
        assert row.tag == "tr", f"Expected tr in nested t_rev_begin, got {row.tag}"
        formats.append(formatter(row))
        texts.append(texter(row))
    return formats, texts
