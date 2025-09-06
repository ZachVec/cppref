import re
from typing import Callable, Optional
from lxml.etree import strip_tags
from lxml.html import HtmlElement

from cppref.core.processor import Processor
from cppref.core.cppreference.utils import nested_table_processor

processor: Processor[[], str] = Processor()


def general(table: HtmlElement, bold: Callable[[HtmlElement], bool], extend: Callable[[int, int], bool]) -> str:  # fmt: off
    title: Optional[str] = None
    for caption in table.iter("caption"):
        assert title is None, "Duplicate title for table"
        title = caption.text_content().strip()
        caption.drop_tree()

    ncols = sum([int(cell.get("colspan", "1")) for cell in table[0]])
    formats, texts, spans = list[str](), list[str](), [0] * ncols
    if title is not None:
        format, text = list[str](), list[str]()
        format.append("cb")
        format.extend(["s"] * (ncols - 1))
        text.append(title)
        text.extend([""] * (ncols - 1))
        formats.append(" ".join(format))
        texts.append(";".join(map(lambda t: f"T{{\n{t}\nT}}", text)))

    for row in table:
        col_index = 0
        format, text = list[str](), list[str]()
        for col in row:
            while spans[col_index] > 0:
                spans[col_index] -= 1
                col_index += 1
                format.append("^")
                text.append("")
            assert col_index < ncols
            rowspan = int(col.get("rowspan", "1"))
            colspan = int(col.get("colspan", "1"))
            spans[col_index] = rowspan - 1
            format.append(f"{'cb' if bold(col) else 'l'}{'x' if extend(col_index, ncols) else ''}")  # fmt: off
            format.extend(["s"] * (colspan - 1))
            text.append(re.sub(r"\n+", "\n.br\n", col.text_content().strip()))
            col_index += colspan
        while col_index < ncols:
            if spans[col_index] > 0:
                spans[col_index] -= 1
                format.append("^")
            else:
                format.append("c")
            col_index += 1
            text.append("")
        formats.append(" ".join(format))
        texts.append(";".join([f"T{{\n{t}\nT}}" for t in text]))

    return f"{'\n'.join(formats)}.\n{'\n'.join(texts)}"


@processor.route()
def _(table: HtmlElement) -> str:
    def bold(element: HtmlElement):
        return element.tag == "th"

    def extend(__index__: int, __total__: int) -> bool:
        return False

    texts: list[str] = list()
    texts.append(".TS")
    texts.append("allbox expand tab(;);")
    texts.append(general(table, bold, extend))
    texts.append(".TE")
    texts.append(".sp")
    return "\n".join(texts)


@processor.route(lambda e: "t-dcl-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    formats, texts = list[str](), list[str]()
    ncols = sum([int(cell.get("colspan", "1")) for cell in table[0]])

    for row in table:
        formats.append(" ".join(["-"] * ncols))  # seperate lines
        format, text = list[str](), list[str]()
        for cnum, col in enumerate(row):
            format.append("lx" if cnum == 0 else "c")
            text.append(re.sub(r"\n+", "\n.br\n", col.text_content().strip()))
        formats.append(" ".join(format))
        texts.append(";".join(map(lambda t: f"T{{\n{t}\nT}}", text)))
    text = f"{'\n'.join(formats)}.\n{'\n'.join(texts)}"

    texts = list()
    texts.append('.SH "SYNOPSIS"')
    texts.append(".TS")
    texts.append("expand tab(;);")
    texts.append(text)
    texts.append(".TE")
    texts.append(".sp")
    texts.append('.SH "DESCRIPTION"')
    return "\n".join(texts)


@processor.route(lambda e: "t-dsc-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    # nested table proceesor
    nt_processor = Processor[[], tuple[list[str], list[list[str]]]]()

    @nt_processor.route(lambda e: "t-rev-begin" in e.get("class", ""))
    def _(table: HtmlElement) -> tuple[list[str], list[list[str]]]:
        def formatter(_: HtmlElement) -> str:
            return "lx l"

        def texter(row: HtmlElement) -> list[str]:
            assert len(row) == 2, f"Expect 2 cols in nested t-rev-begin, got {len(row)}"
            return [r.text_content().strip() for r in row]

        return nested_table_processor(table, formatter, texter)

    @nt_processor.route(lambda e: "t-dsc-begin" in e.get("class", ""))
    def _(table: HtmlElement) -> tuple[list[str], list[list[str]]]:
        def formatter(row: HtmlElement) -> str:
            return "lb lbx" if "t-dsc-hitem" == row.get("class") else "l l"

        def texter(row: HtmlElement) -> list[str]:
            assert len(row) == 2, f"Expect 2 cols in nested t-rev-begin, got {len(row)}"
            return [r.text_content().strip() for r in row]

        return nested_table_processor(table, formatter, texter)

    @nt_processor.route(lambda e: "t-dcl-begin" in e.get("class", ""))
    def _(table: HtmlElement) -> tuple[list[str], list[list[str]]]:
        for row in table.find_class("t-dcl-sep"):
            row.drop_tree()

        def formatter(_: HtmlElement) -> str:
            return "lx l"

        def texter(row: HtmlElement) -> list[str]:
            assert len(row) == 3, f"Expect 3 cols in nested t-rev-begin, got {len(row)}"
            text = list[str]()
            text.append(re.sub(r"\n+", "\n.br\n", row[0].text_content().strip()))
            text.append(row[2].text_content().strip())
            return text

        return nested_table_processor(table, formatter, texter)

    def process_column1(column: HtmlElement) -> tuple[str, list[str]]:
        tlines, text = column.find_class("t-lines"), list[str]()
        if len(tlines) == 0:
            format = "l s"
            text.append(column.text_content().strip())
        elif len(tlines) == 1:
            format = "l s"
            text.append("\n.br\n".join([s.text_content().strip() for s in tlines[0]]))
        elif len(tlines) == 2:
            format = "l l"
            text.append("\n.br\n".join([s.text_content().strip() for s in tlines[0]]))
            text.append("\n.br\n".join([s.text_content().strip() for s in tlines[1]]))
        else:
            assert False, f"Expect len(tlines) == 2, but got {len(tlines)=}"
        return format, text

    def process_column2(column: HtmlElement) -> tuple[list[str], list[list[str]]]:
        nested_tables = list(column.iterchildren("table"))
        if len(nested_tables) == 0:
            format = "lx s"
            text = re.sub(r"\n+", "\n.br\n", column.text_content().strip())
            return [format], [[text]]
        formats, texts, hanging = list[str](), list[list[str]](), list[str]()
        if column.text is not None and len(column.text.strip()) > 0:
            hanging.append(column.text)
        for element in column:
            if element.tag == "table":
                if len(hanging) > 0:
                    hanging = "".join(hanging).strip()
                    if len(hanging) > 0:
                        formats.append("l s")
                        texts.append([re.sub(r"\n+", "\n.br\n", "".join(hanging))])
                    hanging = list()

                f, t = nt_processor.process(element)
                formats.extend(f)
                texts.extend(t)
            else:
                hanging.append(element.text_content())
            if element.tail is not None:
                hanging.append(element.tail)

        if len(hanging):
            hanging = "".join(hanging).strip()
            if len(hanging) > 0:
                formats.append("l s")
                texts.append([re.sub(r"\n+", "\n.br\n", hanging)])

        return formats, texts

    formats, texts = list[str](), list[str]()
    for row in table:
        assert row.tag == "tr", f"Expect table row in table, but got {row.tag}"
        formats.append("- - | - -")
        if len(row) == 1:
            formats.append("cbd s s s")
            formats.append("^ s s s")
            texts.append(f"T{{\n{row[0].text_content().strip()}\nT}}")
            texts.append(f"T{{\n{''}\nT}}")
            continue
        assert len(row) == 2
        col1format, col1text = process_column1(row[0])
        col2format, col2text = process_column2(row[1])
        formats.append(" | ".join([col1format, col2format[0]]))
        texts.append(";".join([f"T{{\n{t}\nT}}" for t in [*col1text, *col2text[0]]]))
        for format, text in zip(col2format[1:], col2text[1:], strict=True):
            formats.append("^ ^ | - -")
            texts.append(";".join(["T{\n\nT}" for _ in range(2)]))
            formats.append(" | ".join(["^ ^", format]))
            texts.append(";".join([f"T{{\n{t}\nT}}" for t in ["", "", *text]]))

    text = f"{'\n'.join(formats[1:])}.\n{'\n'.join(texts)}"
    texts = list()
    texts.append(".TS")
    texts.append("box expand tab(;);")
    texts.append(text)
    texts.append(".TE")
    return "\n".join(texts)


@processor.route(lambda e: "t-par-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    ncols = sum([int(cell.get("colspan", "1")) for cell in table[0]])
    if ncols != 3:
        return ".I There is a ill-formed parameter table."

    texts = list[str]()
    for row in table:
        text = list[str]()
        for col in row:
            text.append(col.text_content().strip())
        texts.append(";".join(map(lambda t: f"T{{\n{t}\nT}}", text)))
    text = "\n".join(texts)

    texts: list[str] = list()
    texts.append(".TS")
    texts.append("expand tab(;);")
    texts.append("rt ct lx.")
    texts.append(text)
    texts.append(".TE")
    texts.append(".sp")
    return "\n".join(texts)


@processor.route(lambda e: "t-rev-begin" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    ncols = sum([int(cell.get("colspan", "1")) for cell in table[0]])
    assert ncols == 2, f"Expect t-rev-begin has 2 columns, got {ncols}"
    formats, texts = list[str](), list[str]()
    for row in table:
        formats.append("lx l")
        text = map(lambda e: e.text_content().strip(), row)
        text = map(lambda t: re.sub(r"\s*\n+\s*", "\n.br\n", t), text)
        texts.append(";".join(map(lambda t: f"T{{\n{t}\nT}}", text)))
    text = f"{'\n'.join(formats)}.\n{'\n'.join(texts)}"

    texts: list[str] = list()
    texts.append(".TS")
    texts.append("box expand tab(;);")
    texts.append(text)
    texts.append(".TE")
    return "\n".join(texts)


@processor.route(lambda e: "dsctable" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    def extend(index: int, total: int) -> bool:
        if total == 3 or total == 4:
            return index == total - 2
        if total < 5:
            return index == total - 1
        return False

    def bold(element: HtmlElement) -> bool:
        return element.tag == "th"

    texts: list[str] = list()
    texts.append(".TS")
    texts.append("allbox expand tab(;);")
    texts.append(general(table, bold, extend))
    texts.append(".TE")
    texts.append(".sp")
    return "\n".join(texts)


@processor.route(lambda e: "wikitable" in e.get("class", ""))
def _(table: HtmlElement) -> str:
    def extend(index: int, total: int) -> bool:
        return total == 3 and index == 1 or total < 5 and index == total - 1

    def bold(element: HtmlElement) -> bool:
        return element.tag == "th"

    text = general(table, bold, extend)
    texts: list[str] = list()
    texts.append(".TS")
    texts.append("allbox expand tab(;);")
    texts.append(text)
    texts.append(".TE")
    texts.append(".sp")
    return "\n".join(texts)


def table(table: HtmlElement):
    strip_tags(table, "tbody")
    if "wikitable" not in table.get("class", ""):
        nested_tables = list(table.iterdescendants("table"))
        nested_classes = ", ".join({t.get("class", "") for t in nested_tables})
        assert len(nested_classes) == 0, (
            f"Unexpected nested table in {table.get('class', '')}: {nested_classes}"
        )
    if len(table) == 0:
        return ""
    if "mw-collapsible" in table.get("class", ""):
        assert False, "Unexpected collapsible table"

    return f"\n{processor.process(table)}\n"
