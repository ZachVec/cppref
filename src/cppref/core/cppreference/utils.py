from typing import Iterable, Optional

from lxml.html import HtmlElement

from cppref.core.processor import Processor


def inline(
    prefix: str,
    first: HtmlElement,
    elements: Iterable[HtmlElement],
    processor: Processor[[], str],
):
    texts: list[str] = [prefix, processor.process(first).strip()]
    if first.tail is not None and len(first.tail.strip()) > 0:
        texts.append(first.tail.strip())
    for e in elements:
        if e.tail is None or len(e.tail.strip()) == 0:
            return f"{''.join(texts).strip()}\n.sp", e
        texts.append(processor.process(e).strip())
    return f"{'\n'.join(texts).strip()}\n.sp", None


def collect(elem: HtmlElement, processor: Processor[[], str]) -> str:
    texts: list[str] = list()
    if elem.text is None or len(elem.text.strip()) == 0:
        prefix: Optional[str] = None
    else:
        prefix: Optional[str] = elem.text
    it = iter(elem)
    for e in it:
        if prefix is not None:
            inlined, hanging = inline(prefix, e, it, processor)
            texts.append(inlined)
            prefix = None
            if hanging is None:
                break
            e = hanging
        elif e.tail is not None and len(e.tail.strip()) > 0:
            prefix = e.tail
        texts.append(processor.process(e))
    if prefix is not None:
        texts.append(prefix)
    return f"{'\n'.join(texts)}\n.sp"
