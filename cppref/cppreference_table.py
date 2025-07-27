import re
from typing import Callable, Optional

from lxml.html import HtmlElement


def cell_wrapper(s: str) -> str:
    return f"T{{\n{s}\nT}}"


def default_table_parser(
    table: HtmlElement,
    format_fn: Optional[Callable[[bool, int, int], str]] = None,
) -> str:
    if format_fn is None:

        def format_fn_normalized(is_th: bool, total: int, index: int) -> str:
            return "cb" if is_th else "l"
    else:

        def format_fn_normalized(is_th: bool, total: int, index: int) -> str:
            return format_fn(is_th, total, index)

    ncols = sum([int(cell.get("colspan", "1")) for cell in table[0]])
    formats, texts = list(), list()
    spans = [0] * ncols
    for row in table:
        col_index = 0
        format, text = list(), list()
        for i, col in enumerate(row):
            while spans[col_index] > 0:
                spans[col_index] -= 1
                col_index += 1
                format.append("^")
                text.append("")
            assert col_index < ncols
            rowspan = int(col.get("rowspan", "1"))
            colspan = int(col.get("colspan", "1"))
            spans[col_index] = rowspan - 1
            format.append(format_fn_normalized(col.tag == "th", ncols, i))
            format.extend(["s"] * (colspan - 1))
            text.append(re.sub("\\s*\n+\\s*", "\n.br\n", col.text_content().strip()))
            col_index += colspan
        formats.append(" ".join(format))
        texts.append(";".join([f"T{{\n{t}\nT}}" for t in text]))
    return f"{'\n'.join(formats)}.\n{'\n'.join(texts)}"


def t_dcl_begin(rows: HtmlElement) -> str:
    # NOTE: Table with this tag is declaration at the very top typically.

    ncols = len(rows[0])
    formats: list[str] = list()
    texts: list[str] = list()

    for row in rows:
        formats.append(" ".join(["-"] * ncols))
        formats.append(" ".join(["lx" if i == 0 else "l" for i in range(ncols)]))
        text = map(lambda c: re.sub("\n+", "\n.br\n", c.text_content().strip()), row)
        texts.append(";".join(map(cell_wrapper, text)))

    return f"{'\n'.join(formats)}.\n{'\n'.join(texts)}"


def t_dsc_begin(rows: HtmlElement) -> str:
    # NOTE:
    # 描述性的表格：应该是只有两列
    # 1. 第一列可能有至多 2 列（目测）t-lines，增加一列后没有发现错误，可能有多列
    # 2. 第二列可能有 t-rev-table，
    def parse_nested_t_rev(nested_rows: HtmlElement) -> str:
        texts: list[str] = list()
        for col1, col2 in nested_rows:
            texts.append(f"{col1.text_content().strip()} {col2.text_content().strip()}")
        return "\n.br\n".join(texts)

    formats: list[str] = list()
    texts: list[str] = list()
    for row in rows:
        formats.append("- - | -")
        if row.get("class") is None:
            formats.append("cbd s s")
            formats.append("^ s s")
            texts.append(cell_wrapper(row[0].text_content().strip()))
            texts.append(cell_wrapper(""))
        else:
            col1, col2 = row[0], row[1]
            # Col1
            tlines = col1.find_class("t-lines")
            text: list[str] = list()
            if len(tlines) == 0:
                text.append(col1.text_content().strip())
                formats.append("l s | lx")
            elif len(tlines) == 1:
                text.append(
                    "\n.br\n".join([span.text_content().strip() for span in tlines[0]])
                )
                formats.append("l s | lx")
            elif len(tlines) == 2:
                text.append(
                    "\n.br\n".join([span.text_content().strip() for span in tlines[0]])
                )
                text.append(
                    "\n.br\n".join([span.text_content().strip() for span in tlines[1]])
                )
                formats.append("l l | lx")
            else:
                assert False
            # Col2
            nested_t_rev_begin = col2.find_class("t-rev-begin")
            if len(nested_t_rev_begin) > 0:
                assert len(nested_t_rev_begin) == 1
                text.append(parse_nested_t_rev(nested_t_rev_begin[0]))
            else:
                text.append(
                    re.sub("\\s*\n+\\s*", "\n.br\n", col2.text_content().strip())
                )
            texts.append(";".join(map(cell_wrapper, text)))
    return f"{'\n'.join(formats[1:])}.\n{'\n'.join(texts)}"


def t_par_begin(table: HtmlElement) -> str:
    # NOTE: Parameter table of 3 columns, with second column being '-'.
    texts: list[str] = list()
    for row in table:
        text: list[str] = list()
        for col in row:
            text.append(col.text_content().strip())
        texts.append(";".join(map(lambda t: f"T{{\n{t}\nT}}", text)))
    return f"rt ct lx.\n{'\n'.join(texts)}"


def t_rev_begin(rows: HtmlElement) -> str:
    # NOTE: 经常被嵌套的表，宽度一定为2，第一列拓宽
    # 增加一列后超出表格边界，应该是宽度一定为 2
    opts: list[str] = list()
    text: list[str] = list()
    assert len(rows) > 0, "empty table"
    for cols in rows:
        assert len(cols) == 2, "t-rev-begin has more than 2 columns"
        opts.append("- -")
        opts.append("lx l")
        text.append(
            ";".join(
                map(
                    lambda col: f"T{{\n{re.sub('\\s*\n+\\s*', '\n.br\n', col.text_content().strip())}\nT}}",
                    cols,
                )
            )
        )
    return f"{'\n'.join(opts[1:])}.\n{'\n'.join(text)}"


def dsctable(rows: HtmlElement) -> str:
    # NOTE: 查看 cppman 代码发现：
    # 1. 如果是 3 列，中间列加宽
    # 2. 如果小于 5 列，则最后一列加宽
    def format_fn(is_th: bool, total: int, index: int) -> str:
        extend = total == 3 and index == 1 or total < 5 and index == total - 1
        return f"""{"cb" if is_th else "l"}{"x" if extend else ""}"""

    return f"{default_table_parser(rows, format_fn)}"


def wikitable(rows: HtmlElement) -> str:
    return dsctable(rows)
