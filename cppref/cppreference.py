import datetime

from lxml import etree, html
from lxml.html import HtmlElement

from .cppreference_table import (
    dsctable,
    t_dcl_begin,
    t_dsc_begin,
    t_par_begin,
    t_rev_begin,
    default_table_parser,
    wikitable,
)
from .processor import Processor

processor = Processor()


@processor.route("p")
def paragraph(tree: HtmlElement) -> str:
    etree.strip_tags(tree, "*")
    return f"{tree.text_content().strip()}\n.sp"


@processor.route("h3")
def section_header(tree: HtmlElement) -> str:
    return rf'.sp{"\n"}.SH "{tree.text_content().strip().upper()}"'


@processor.route("ol")
def ordered_list(tree: HtmlElement) -> str:
    r"""
    .nr step 0 1
    .nr PI 3n
    A numbered list:
    .IP \n+[step]
    lawyers
    .IP \n+[step]
    guns
    .IP \n+[step]
    money
    .LP
    """
    lines: list[str] = list()
    lines.append(r".nr step 0 1")
    lines.append(r".nr PI 3n")
    for item in tree:
        assert item.tag == "li", f"Unknown tag {item.tag} in ordred list"
        lines.append(r".IP \n+[step]")
        text = "".join(item.text_content()).strip()
        lines.append(rf"{text}")
    lines.append(r".LP")
    return "\n".join(lines)


@processor.route("ul")
def unordered_list(tree: HtmlElement) -> str:
    r"""Example:
    .nr PI 2n
    A bulleted list:
    .IP \[bu]
    lawyers
    .IP \[bu]
    guns
    .IP \[bu]
    money
    """
    lines: list[str] = list()
    for item in tree:
        assert item.tag == "li", f"Unknown tag {item.tag} in unordered list"
        lines.append(r".IP \[bu]")
        text = "".join(item.text_content()).strip()
        lines.append(rf"{text}")
    lines.append(r".LP")
    return "\n".join(lines)


@processor.route("div")
def div(tree: HtmlElement) -> str:
    if "t-example" in tree.get("class", ""):
        elem = tree.xpath("div[@class='t-example-live-link']")[0]
        tree.remove(elem)

        return f".nf\n{tree.text_content().replace('\\', r'\e')}"

    etree.strip_tags(tree, "*")
    if "t-li1" in tree.get("class", ""):
        return f"{tree.text_content().strip()}\n.sp"
    return tree.text_content().strip()


@processor.route("table")
def table(tree: HtmlElement) -> str:
    table_type = tree.get("class", None)
    assert table_type is not None
    table_type = table_type.split(" ")
    etree.strip_tags(tree, "tbody")
    if "t-dcl-begin" in table_type:
        texts = [
            '.SH "SYNOPSIS"',
            ".TS",
            "expand tab(;);",
            f"{t_dcl_begin(tree)}",
            ".TE",
            ".sp",
            '.SH "DESCRIPTION"',
        ]
        return "\n".join(texts)
    if "t-dsc-begin" in table_type:
        texts = (".TS", "box expand tab(;);", f"{t_dsc_begin(tree)}", ".TE")
        return "\n".join(texts)
    if "t-par-begin" in table_type:
        texts = (".TS", "expand tab(;);", f"{t_par_begin(tree)}", ".TE", ".sp")
        return "\n".join(texts)
    if "t-rev-begin" in table_type:
        texts = (".TS", "box expand tab(;);", f"{t_rev_begin(tree)}", ".TE")
        return "\n".join(texts)
    if "dsctable" in table_type:
        texts = (".TS", "allbox expand tab(;);", f"{dsctable(tree)}", ".TE", ".sp")
        return "\n".join(texts)
    if "wikitable" in table_type:
        texts = (".TS", "allbox expand tab(;);", f"{wikitable(tree)}", ".TE", ".sp")
        return "\n".join(texts)
    return f".TS\nallbox expand tab(;);\n{default_table_parser(tree)}\n.TE\n.sp"


def process(document: str) -> str:
    # fmt: off
    doc: HtmlElement = html.fromstring(document, parser=html.HTMLParser(encoding="utf-8"))
    doc = doc.xpath("/html/body/div[@id='cpp-content-base']/div[@id='content']")[0]
    body: HtmlElement = doc.xpath("div[@id='bodyContent']/div[@id='mw-content-text']")[0]
    # fmt: on
    heading: HtmlElement = doc.xpath("h1")[0]
    texts: list[str] = list()
    heading_text = heading.text_content().strip()
    date = str(datetime.date.today())
    source = "cppreference.com"
    slogan = "C++ Programmer\\'s Manual"
    texts.append(f'.TH {heading_text} 3 "{date}" "{source}" "{slogan}"')
    texts.append(f'.SH "NAME"\n{heading_text}')
    body.remove(body.xpath("div[@class='t-navbar']")[0])
    body.remove(body.xpath("table[@id='toc']")[0])

    for element in body.find_class("editsection"):
        # NOTE: remove the invisible 'edit' text
        element.drop_tree()

    for element in body.find_class("ambox"):
        # NOTE: remove the incomplete section notice
        element.drop_tree()

    for element in filter(lambda e: isinstance(e.tag, str), body):
        texts.append(processor.process(element))

    unicode_mappings: list[tuple[str, str]] = [
        ("\xa0", " "),  # replace(&nbsp) with space
        ("\u200b", ""),  # remove zerowidthspace
    ]
    ret = "\n".join(texts)
    for char, repl in unicode_mappings:
        ret = ret.replace(char, repl)
    return ret
