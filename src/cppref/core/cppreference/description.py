import re
from lxml.html import HtmlElement

from cppref.core.cppreference.utils import collect
from cppref.core.processor import Processor


def dl(desc: HtmlElement, processor: Processor[[], str]) -> str:
    p = processor.clone()

    level: int = 2

    @p.route(lambda e: e.tag == "dl")
    def _(elem: HtmlElement) -> str:
        nonlocal level
        level += 1
        text = collect(elem, p)
        level -= 1
        return text

    @p.route(lambda e: e.tag == "dt")
    def _(elem: HtmlElement) -> str:
        return f"{elem.text_content().strip()}\n"

    @p.route(lambda e: e.tag == "dd")
    def _(elem: HtmlElement) -> str:
        # INFO: dd is actually the same as dl, the only difference is
        # dl increase indent level, but dd will not.
        return collect(elem, p)

    @p.route(lambda e: e.tag == "ul")
    def _(elem: HtmlElement) -> str:
        texts: list[str] = list()
        texts.append(f".RS {2 * level}")
        for item in elem:
            assert item.tag == "li", f"Unknown tag {item.tag} in unordered list"
            texts.append(r'.IP "◦" 2n')
            texts.append(f"{item.text_content().strip()}")
        texts.append(r".RE")
        return f"\n{'\n'.join(texts)}\n"

    @p.route(lambda e: e.tag == "ol")
    def _(elem: HtmlElement) -> str:
        texts = list[str]()
        texts.append(rf".nr step{level} 0 1")
        texts.append(f".RS {2 * level}")
        for item in elem:
            assert item.tag == "li", f"Unknown tag {item.tag} in ordered list"
            texts.append(rf".IP \n+[step{level}] 2n")
            texts.append(rf"{item.text_content().strip()}")
        texts.append(r".RE")
        return f"\n{'\n'.join(texts)}\n"

    @p.route(lambda e: e.tag in ("i", "sup"))
    def _(elem: HtmlElement) -> str:
        return f'.I "{elem.text_content().strip()}"\n'

    @p.route()
    def _(elem: HtmlElement) -> str:
        return f"{elem.text_content().strip()}\n.sp"

    return re.sub(r"\n+", "\n", collect(desc, p))
