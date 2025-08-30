import datetime

from lxml import etree, html

from cppref.core.cppreference.description import description
from cppref.core.processor import Processor

processor: Processor[[], str] = Processor()


@processor.route(lambda e: e.tag == "h1")
def header1(elem: html.HtmlElement) -> str:
    return (
        ".TS\n"
        f"expand tab(;);\n"
        f"- - -\n"
        f"c s s\n"
        f"- - -\n"
        f"c s s.\n"
        f"T{{\n{elem.text_content().strip()}\nT}}\n"
        f" ; ;\n"
        ".TE\n"
        ".sp"
    )


@processor.route(lambda e: e.tag == "h2")
def header2(elem: html.HtmlElement) -> str:
    return (
        ".TS\n"
        f"expand tab(;);\n"
        f"l s s\n"
        f"- - -\n"
        f"c s s.\n"
        f"T{{\n{elem.text_content().strip()}\nT}};\n"
        f" ; ; \n"
        ".TE\n"
        ".sp"
    )


@processor.route(lambda e: e.tag == "h3")
def section(s: html.HtmlElement) -> str:
    return f'.sp\n.SH "{s.text_content().strip().upper()}"'


@processor.route(lambda e: e.tag in ("h4", "h5"))
def subsection(elem: html.HtmlElement) -> str:
    return f'.sp\n.SS "{elem.text_content().strip()}"'


@processor.route(lambda e: e.tag == "pre")
def pre(elem: html.HtmlElement) -> str:
    return f".in +2n\n.nf\n{elem.text_content().strip()}\n.fi\n.in\n.sp"


@processor.route(lambda e: e.tag == "p")
def paragraph(p: html.HtmlElement) -> str:
    etree.strip_tags(p, "*")
    return f"{p.text_content().strip()}\n.sp"


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
    return f"{elem.text_content().strip()}\n.sp"


@processor.route(lambda e: e.tag == "br")
def br(_: html.HtmlElement) -> str:
    return "\n.sp"


@processor.route(lambda e: e.tag == "ol")
def ordered_list(ol: html.HtmlElement) -> str:
    lines: list[str] = list()
    lines.append(r".nr step 0 1")
    lines.append(r".nr PI 3n")
    for item in ol:
        assert item.tag == "li", f"Unknown tag {item.tag} in ordred list"
        lines.append(r".IP \n+[step]")
        text = "".join(item.text_content()).strip()
        lines.append(rf"{text}")
    lines.append(r".LP")
    return "\n".join(lines)


@processor.route(lambda e: e.tag == "ul")
def unordered_list(ul: html.HtmlElement) -> str:
    lines: list[str] = list()
    for item in ul:
        assert item.tag == "li", f"Unknown tag {item.tag} in unordered list"
        lines.append('.IP "•" 2n')
        lines.append(item.text_content().strip())
    lines.append(r".LP")
    return "\n".join(lines)


@processor.route(lambda e: e.tag == "div")
def div(elem: html.HtmlElement) -> str:
    # if "t-example" in tree.get("class", ""):
    #     elem = tree.xpath("div[@class='t-example-live-link']")[0]
    #     tree.remove(elem)
    #
    #     return f".nf\n{tree.text_content().replace('\\', r'\e')}"
    #
    # etree.strip_tags(tree, "*")
    # if "t-li1" in tree.get("class", ""):
    #     return f"{tree.text_content().strip()}\n.sp"
    # return tree.text_content().strip()
    return ""


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

    hanging_texts: list[str] = list()
    for element in filter(lambda e: isinstance(e.tag, str), body):
        if element.tail is not None and len(element.tail.strip()) > 0:
            if len(hanging_texts) > 0:
                hanging_texts.append(p.process(element))
                hanging_texts.append(element.tail)
            else:
                texts.append(p.process(element))
                hanging_texts.append(element.tail)
        else:
            if len(hanging_texts) > 0:
                texts.append(f"{''.join(hanging_texts).strip()}\n.sp")
                hanging_texts = list()
            texts.append(p.process(element))

    if len(hanging_texts) > 0:
        texts.append(f"{''.join(hanging_texts).strip()}\n.sp")
        hanging_texts = list()

    unicode_mappings: list[tuple[str, str]] = [
        ("\xa0", " "),  # replace(&nbsp) with space
        ("\u200b", ""),  # remove zerowidthspace
        ("\ufeff", ""),  # remove invisible zerowidthspace
    ]
    ret = "\n".join(texts)
    for char, repl in unicode_mappings:
        ret = ret.replace(char, repl)
    return ret
