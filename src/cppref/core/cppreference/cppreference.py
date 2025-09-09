import datetime
import re

from lxml import etree, html

from cppref.core.cppreference.description import dl
from cppref.core.cppreference.div import div
from cppref.core.cppreference.utils import collect
from cppref.core.cppreference.table import table
from cppref.core.processor import Processor

processor: Processor[[], str] = Processor()


@processor.route(lambda e: e.tag == "h1")
def _(elem: html.HtmlElement) -> str:
    return (
        "\n.sp\n"
        ".TS\n"
        f"expand tab(;);\n"
        f"- - -\n"
        f"c s s\n"
        f"- - -\n"
        f"c s s.\n"
        f"T{{\n{elem.text_content().strip()}\nT}}\n"
        f" ; ;\n"
        ".TE\n"
    )


@processor.route(lambda e: e.tag == "h2")
def _(elem: html.HtmlElement) -> str:
    return (
        "\n.sp\n"
        ".TS\n"
        f"expand tab(;);\n"
        f"l s s\n"
        f"- - -\n"
        f"c s s.\n"
        f"T{{\n{elem.text_content().strip()}\nT}};\n"
        f" ; ; \n"
        ".TE\n"
    )


@processor.route(lambda e: e.tag == "h3")
def _(s: html.HtmlElement) -> str:
    return f'\n.sp\n.SH "{s.text_content().strip().upper()}"\n'


@processor.route(lambda e: e.tag in ("h4", "h5"))
def _(elem: html.HtmlElement) -> str:
    return f'\n.sp\n.SS "{elem.text_content().strip()}"\n'


@processor.route(lambda e: e.tag == "pre")
def _(elem: html.HtmlElement) -> str:
    return f"\n.in +2n\n.nf\n{elem.text_content().strip()}\n.fi\n.in\n"


@processor.route(lambda e: e.tag == "p")
def _(p: html.HtmlElement) -> str:
    return f"\n{p.text_content().replace('\n', '\n.br\n')}\n"


@processor.route(lambda e: e.tag == "span")
def _(elem: html.HtmlElement) -> str:
    return elem.text_content().strip()


@processor.route(lambda e: e.tag == "dl")
def _(elem: html.HtmlElement) -> str:
    return dl(elem, processor)


@processor.route(lambda e: e.tag == "code")
def _(elem: html.HtmlElement) -> str:
    return elem.text_content().strip()


@processor.route(lambda e: e.tag == "a")
def _(elem: html.HtmlElement) -> str:
    return elem.text_content().strip()


@processor.route(lambda e: e.tag == "br")
def _(_: html.HtmlElement) -> str:
    return "\n.br\n"


@processor.route(lambda e: e.tag == "ol")
def _(ol: html.HtmlElement) -> str:
    lines: list[str] = list()
    lines.append(r".nr step 0 1")
    for item in ol:
        assert item.tag == "li", f"Unknown tag {item.tag} in ordred list"
        lines.append(r".IP \n+[step] 2")
        text = "".join(item.text_content()).strip()
        lines.append(rf"{text}")
    lines.append(r".LP")
    return f"\n{'\n'.join(lines)}\n"


@processor.route(lambda e: e.tag == "ul")
def _(ul: html.HtmlElement) -> str:
    lines: list[str] = list()
    for item in ul:
        assert item.tag == "li", f"Unknown tag {item.tag} in unordered list"
        lines.append('.IP "•" 2n')
        lines.append(item.text_content().strip())
    lines.append(r".LP")
    return f"\n{'\n'.join(lines)}\n"


@processor.route(lambda e: e.tag == "div")
def _(element: html.HtmlElement) -> str:
    if "t-member" in element.get("class", ""):
        for e in element.iter("h2"):
            e.drop_tree()
        return collect(element, processor)
    if element.get("class") is None:
        return collect(element, processor)

    if re.search(r"t-ref-std-c\+\+\d\d", element.get("class", "")) is not None:
        return collect(element, processor)

    if "mw-collapsed" in element.get("class", ""):
        etree.strip_tags(element, "div")
        return collect(element, processor)

    return div(element)


@processor.route(lambda e: e.tag == "table")
def _(elem: html.HtmlElement) -> str:
    return table(elem)


def process(document: str, url: str, p: Processor[[], str] = processor) -> str:
    doc: html.HtmlElement = html.fromstring(document, parser=html.HTMLParser(encoding="utf-8"))  # fmt: off
    doc = doc.xpath("/html/body/div[@id='cpp-content-base']/div[@id='content']")[0]
    body: html.HtmlElement = doc.xpath("div[@id='bodyContent']/div[@id='mw-content-text']")[0]  # fmt: off
    heading: html.HtmlElement = doc.xpath("h1")[0]
    texts: list[str] = list()
    heading_text = heading.text_content().strip()
    date = str(datetime.date.today())
    source = url
    slogan = "C++ Programmer\\'s Manual"
    texts.append(f'.TH "{heading_text}" 3 "{date}" "{source}" "{slogan}"')
    texts.append('.SH "DEFINITION"')

    # remove the table of contents which does not make sense
    for element in body.xpath("//*[@id='toc']"):
        element.drop_tree()

    # remove all the comments
    for element in body.xpath("//comment()"):
        element.drop_tree()

    # remove navigation bars at the top
    for element in body.find_class("t-navbar"):
        element.drop_tree()

    for element in body.find_class("t-page-template"):
        element.drop_tree()

    # remove the invisible edit text
    for element in body.find_class("editsection"):
        element.drop_tree()

    # remove invisible elements
    for element in body.find_class("noprint"):
        element.drop_tree()

    # remove the incomplete section notice
    for element in body.find_class("ambox"):
        element.drop_tree()

    # remove images
    for element in body.find_class("t-image"):
        element.drop_tree()

    # remove images
    for element in body.find_class("t-inheritance-diagram"):
        element.drop_tree()

    for element in body.find_class("t-plot"):
        element.drop_tree()

    for element in body.find_class("t-template-editlink"):
        element.drop_tree()

    for element in body.cssselect("[style]"):
        if "display:none" in element.get("style", ""):
            element.drop_tree()

    for element in body.xpath('.//table[contains(@class, "mw-collapsible") or contains(@class, "mw-collapsed")]'):  # fmt: off
        span = html.Element("span")
        span.text = "There should be a table, but it's too crowded."
        parent = element.getparent()
        if parent is not None:
            index = parent.index(element)
            parent.remove(element)
            parent.insert(index, span)

    texts.append(collect(body, p))

    text = "\n.sp\n".join(texts)

    return text.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")
