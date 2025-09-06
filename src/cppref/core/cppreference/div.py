import re
from lxml.etree import strip_tags
from lxml.html import HtmlElement

from cppref.core.processor import Processor


processor = Processor[[], str]()


@processor.route(lambda e: "t-example" in e.get("class", ""))
def _(element: HtmlElement) -> str:
    # remove 'run this code' button
    for e in element.find_class("t-example-live-link"):
        e.drop_tree()
    return f"\n.nf\n{element.text_content().replace('\\', r'\e')}\n"


@processor.route(lambda e: "mw-geshi" in e.get("class", ""))
def _(element: HtmlElement) -> str:
    return f"\n.nf\n{element.text_content().replace('\\', r'\e')}\n"


@processor.route(lambda e: "t-noexcept-full" in e.get("class", ""))
def _(element: HtmlElement) -> str:
    return f"\n.nf\n{element.text_content().replace('\\', r'\e')}\n"


@processor.route(lambda e: "t-noexcept-inline" in e.get("class", ""))
def _(element: HtmlElement) -> str:
    return element.text_content().strip()


@processor.route(lambda e: "t-inherited" in e.get("class", ""))
def _(element: HtmlElement) -> str:
    h2 = element.find(".//h2")
    assert h2 is not None, "Get non h2 in t-inherited"
    return h2.text_content().strip()


@processor.route(lambda e: "t-li" in e.get("class", ""))
def _(element: HtmlElement) -> str:
    matched = re.search(r"t-li(\d)", element.get("class", ""))
    assert matched is not None, "t-li suffixed with no number"
    level = int(matched.group(1))
    return f"\n.in +{2 * level}n \n{element.text_content().strip()}\n.in\n"


@processor.route(lambda e: "mainpagediv" in e.get("class", ""))
def _(element: HtmlElement) -> str:
    # For https://en.cppreference.com/w/cpp/index.html
    strip_tags(element, "p")
    return (
        f"\n.in +2n\n{element.text_content().strip().replace('\n', '\n.br\n')}\n.in\n"
    )


def div(element: HtmlElement) -> str:
    return processor.process(element)
