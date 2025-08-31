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
