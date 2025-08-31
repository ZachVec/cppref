import datetime
import re

from lxml import etree, html

from cppref.core.cppreference.description import description
from cppref.core.cppreference.div import div_block
from cppref.core.cppreference.utils import collect
from cppref.core.processor import Processor

processor: Processor[[], str] = Processor()


@processor.route(lambda e: e.tag == "h1")
def header1(elem: html.HtmlElement) -> str:
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
def header2(elem: html.HtmlElement) -> str:
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
def section(s: html.HtmlElement) -> str:
    return f'\n.sp\n.SH "{s.text_content().strip().upper()}"\n'


@processor.route(lambda e: e.tag in ("h4", "h5"))
def subsection(elem: html.HtmlElement) -> str:
    return f'\n.sp\n.SS "{elem.text_content().strip()}"\n'


@processor.route(lambda e: e.tag == "pre")
def pre(elem: html.HtmlElement) -> str:
    return f"\n.in +2n\n.nf\n{elem.text_content().strip()}\n.fi\n.in\n"


@processor.route(lambda e: e.tag == "p")
def paragraph(p: html.HtmlElement) -> str:
    return f"\n{p.text_content().replace('\n', '\n.br\n')}\n"


@processor.route(lambda e: e.tag == "span")
def span(elem: html.HtmlElement) -> str:
    return elem.text_content().strip()


@processor.route(lambda e: e.tag == "dl")
def dl(elem: html.HtmlElement) -> str:
    return description(elem, processor)


@processor.route(lambda e: e.tag == "code")
def code(elem: html.HtmlElement) -> str:
    return elem.text_content().strip()


@processor.route(lambda e: e.tag == "a")
def a(elem: html.HtmlElement) -> str:
    return elem.text_content().strip()


@processor.route(lambda e: e.tag == "br")
def br(_: html.HtmlElement) -> str:
    return "\n.br\n"


@processor.route(lambda e: e.tag == "ol")
def ordered_list(ol: html.HtmlElement) -> str:
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
def unordered_list(ul: html.HtmlElement) -> str:
    lines: list[str] = list()
    for item in ul:
        assert item.tag == "li", f"Unknown tag {item.tag} in unordered list"
        lines.append('.IP "•" 2n')
        lines.append(item.text_content().strip())
    lines.append(r".LP")
    return f"\n{'\n'.join(lines)}\n"


@processor.route(lambda e: e.tag == "div")
def div(element: html.HtmlElement) -> str:
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

    return div_block(element)


@processor.route(lambda e: e.tag == "table")
def table(elem: html.HtmlElement) -> str:
    #     table_type = tree.get("class", None)
    #     assert table_type is not None
    #     table_type = table_type.split(" ")
    #     etree.strip_tags(tree, "tbody")
    #     if "t-dcl-begin" in table_type:
    #         texts = [
    #             '.SH "SYNOPSIS"',
    #             ".TS",
    #             "expand tab(;);",
    #             f"{t_dcl_begin(tree)}",
    #             ".TE",
    #             ".sp",
    #             '.SH "DESCRIPTION"',
    #         ]
    #         return "\n".join(texts)
    #     if "t-dsc-begin" in table_type:
    #         texts = (".TS", "box expand tab(;);", f"{t_dsc_begin(tree)}", ".TE")
    #         return "\n".join(texts)
    #     if "t-par-begin" in table_type:
    #         texts = (".TS", "expand tab(;);", f"{t_par_begin(tree)}", ".TE", ".sp")
    #         return "\n".join(texts)
    #     if "t-rev-begin" in table_type:
    #         texts = (".TS", "box expand tab(;);", f"{t_rev_begin(tree)}", ".TE")
    #         return "\n".join(texts)
    #     if "dsctable" in table_type:
    #         texts = (".TS", "allbox expand tab(;);", f"{dsctable(tree)}", ".TE", ".sp")
    #         return "\n".join(texts)
    #     if "wikitable" in table_type:
    #         texts = (".TS", "allbox expand tab(;);", f"{wikitable(tree)}", ".TE", ".sp")
    #         return "\n".join(texts)
    #     # if "mainpagetable" in table_type:
    #     #     ...
    #     return f".TS\nallbox expand tab(;);\n{default_table_parser(tree)}\n.TE\n.sp"
    return ""


def process(document: str, p: Processor[[], str] = processor) -> str:
    # fmt: off
    doc: html.HtmlElement = html.fromstring(document, parser=html.HTMLParser(encoding="utf-8"))
    doc = doc.xpath("/html/body/div[@id='cpp-content-base']/div[@id='content']")[0]
    body: html.HtmlElement = doc.xpath("div[@id='bodyContent']/div[@id='mw-content-text']")[0]
    # fmt: on
    heading: html.HtmlElement = doc.xpath("h1")[0]
    texts: list[str] = list()
    heading_text = heading.text_content().strip()
    date = str(datetime.date.today())
    source = "cppreference.com"
    slogan = "C++ Programmer\\'s Manual"
    texts.append(f'.TH "{heading_text}" 3 "{date}" "{source}" "{slogan}"')
    texts.append(f'.SH "{heading_text}"')

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

    texts.append(collect(body, p))

    text = "\n.sp\n".join(texts)

    return text.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")
