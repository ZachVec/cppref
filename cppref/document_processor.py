import datetime

from lxml import etree, html
from lxml.html import HtmlElement


class DocumentProcessor:
    def __init__(self, data: str):
        # fmt: off
        doc: HtmlElement = html.fromstring(data, parser=html.HTMLParser(encoding="utf-8"))
        doc = doc.xpath("/html/body/div[@id='cpp-content-base']/div[@id='content']")[0]
        self.body: HtmlElement = doc.xpath("div[@id='bodyContent']/div[@id='mw-content-text']")[0]
        # fmt: on
        heading: HtmlElement = doc.xpath("h1")[0]
        self.text: list[str] = list()
        heading_text = heading.text_content().strip()
        date = str(datetime.date.today())
        source = "cppreference.com"
        slogan = "C++ Programmer\\'s Manual"
        self.text.append(f'.TH {heading_text} 3 "{date}" "{source}" "{slogan}"')
        self.text.append(f'.SH "NAME"\n{heading_text}')

    def process(self) -> str:
        self.body.remove(self.body.xpath("div[@class='t-navbar']")[0])
        self.body.remove(self.body.xpath("table[@id='toc']")[0])
        for element in self.body:  # skip navbar
            if not isinstance(element.tag, str):
                continue
            text = self._process(element.tag, element)
            self.text.append(text)
        return "\n.sp\n".join(self.text)

    def _process(self, tag: str, tree: html.HtmlElement) -> str:
        if tag == "p":
            etree.strip_tags(tree, "*")
            return tree.text_content().strip()
        elif tag == "h3":  # DONE
            return rf'.SH "{tree.text_content().strip().upper()}"'
        elif tag == "ol":  # DONE
            return self._ordered_list(tree)
        elif tag == "ul":  # DONE
            return self._unordered_list(tree)
        elif tag == "table":
            return self._table(tree)
        elif tag == "div":
            return self._div(tree)
        else:
            raise ValueError("Unknown tag")

    def _ordered_list(self, tree: HtmlElement) -> str:
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
            text = "".join(filter(lambda c: ord(c) < 128, item.text_content())).strip()
            lines.append(rf"{text}")
        lines.append(r".LP")
        return "\n".join(lines)

    def _unordered_list(self, tree: HtmlElement) -> str:
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
            text = "".join(filter(lambda c: ord(c) < 128, item.text_content())).strip()
            lines.append(rf"{text}")
        lines.append(r".LP")
        return "\n".join(lines)

    def _table(self, tree: HtmlElement) -> str:
        table_type = tree.get("class", None)
        assert table_type is not None
        table_type = table_type.split(" ")
        etree.strip_tags(tree, "tbody")
        table: list[HtmlElement] = tree.xpath("tr")
        # TODO: parse the following tables
        # if "t-dcl-begin" in table_type:
        #     return ""
        # if "t-dsc-begin" in table_type:
        #     return ""
        # if "dsctable" in table_type:
        #     return ""
        # if "t-rev-begin" in table_type:
        #     return ""
        # if "wikitable" in table_type:
        #     return ""
        # if "t-par-begin" in table_type:
        #     return ""
        # assert False, "Unknown table type"

        nrows = len(table)
        ncols = len(table[0])
        ret = [["" for _ in range(ncols)] for _ in range(nrows)]
        for rnum, row in enumerate(table):
            for cnum, col in enumerate(row):
                text = col.text_content().strip().replace(";", r"\;")
                ret[rnum][cnum] = f"T{{\n{text}\nT}}"
        return (
            ".TS\n"
            "allbox expand tab(;);\n"
            f"{' '.join(['l'] * ncols)}.\n"
            f"{'\n'.join(map(';'.join, ret))}\n"
            ".TE\n"
        )

    def _div(self, tree: HtmlElement) -> str:
        if "t-example" in tree.get("class", ""):
            elem = tree.xpath("div[@class='t-example-live-link']")[0]
            tree.remove(elem)

            return f".nf\n{tree.text_content().replace(r'\\n', r'\en')}"
        etree.strip_tags(tree, "*")
        return tree.text_content().strip()
