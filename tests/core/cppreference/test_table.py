import unittest
from typing import Callable

from lxml.etree import strip_tags
from lxml.html import HtmlElement, HTMLParser, fromstring

from cppref.conf import ConfContext
from cppref.typing_ import Record
from cppref.utils import Utils
from tests.helpers import TestBase


@unittest.skip("Demonstrating the table structure")
class CppReferenceAssumption(TestBase):
    def setUp(self):
        root = self.get_root().joinpath("testdata")
        root.mkdir(parents=True, exist_ok=True)
        state = root.joinpath("state")
        cache = root.joinpath("share")
        state.mkdir(parents=True, exist_ok=True)
        cache.mkdir(parents=True, exist_ok=True)
        self._environs = {"XDG_STATE_HOME": str(state), "XDG_DATA_HOME": str(cache)}

    def test_assumptions(self):
        dbfile = self.get_root().joinpath("testdata", "index.db")
        records = Utils.query("cppreference", dbfile)

        with ConfContext() as conf:
            root = conf.folder.joinpath("cppreference", "html")

        def toElement(record: Record) -> HtmlElement:
            doc = Utils.read_file(root.joinpath(f"{record.id}.html"))
            doc = fromstring(doc, parser=HTMLParser(encoding="utf-8"))
            doc = doc.xpath("/html/body/div[@id='cpp-content-base']/div[@id='content']")[0]  # fmt: off
            doc = doc.xpath("div[@id='bodyContent']/div[@id='mw-content-text']")[0]
            # remove the table of contents which does not make sense
            for element in doc.xpath("//*[@id='toc']"):
                element.drop_tree()

            # remove all the comments
            for element in doc.xpath("//comment()"):
                element.drop_tree()

            # remove navigation bars at the top
            for element in doc.find_class("t-navbar"):
                element.drop_tree()

            for element in doc.find_class("t-page-template"):
                element.drop_tree()

            # remove the invisible edit text
            for element in doc.find_class("editsection"):
                element.drop_tree()

            # remove invisible elements
            for element in doc.find_class("noprint"):
                element.drop_tree()

            # remove the incomplete section notice
            for element in doc.find_class("ambox"):
                element.drop_tree()

            for element in doc.find_class("fmbox"):
                element.drop_tree()

            # remove images
            for element in doc.find_class("t-image"):
                element.drop_tree()

            # remove images
            for element in doc.find_class("t-inheritance-diagram"):
                element.drop_tree()

            for element in doc.find_class("t-plot"):
                element.drop_tree()

            for element in doc.find_class("t-template-editlink"):
                element.drop_tree()

            for element in doc.cssselect("[style]"):
                if "display:none" in element.get("style", ""):
                    element.drop_tree()

            for element in doc.xpath('.//table[contains(@class, "mw-collapsible") or contains(@class, "mw-collapsed")]'):  # fmt: off
                element.drop_tree()

            return doc

        for record, document in map(lambda r: (r, toElement(r)), records):
            with self.subTest(f"Record={record}, url={record.url}"):
                for table in document.iterdescendants("table"):
                    self.table_assumptions(table)

    def table_assumptions(self, table: HtmlElement):
        strip_tags(table, "tbody")
        clazz = table.get("class", "")
        if len(table) == 0 or clazz == "" or len(table.text_content().strip()) == 0:
            return
        # self.assertNotEqual(clazz, "", table.text_content())
        assumptions = list[Callable[[HtmlElement], None]]()
        if "t-dcl-begin" in clazz:
            assumptions.append(self.assume_columns_of(3))
        elif "t-par-begin" in clazz:
            assumptions.append(self.assume_columns_of(3))
        elif "t-dsc-begin" in clazz:
            assumptions.append(self.assume_columns_of(2))
        elif "t-rev-begin" in clazz:
            assumptions.append(self.assume_columns_of(2))
        elif "t-sdsc-begin" in clazz:
            assumptions.append(self.assume_columns_of(3))
            for e in table.find_class("t-sdsc-sep"):
                parent = e.getparent()
                if parent is None:
                    self.assertTrue(False, "Expected a parent, got None")
                else:
                    self.assertEqual(len(parent), 1, "Expected t-sdsc-sep has no siblings")  # fmt: off
                    parent.drop_tree()
        elif "eq-fun-cpp-table" in clazz:
            assumptions.append(self.assume_columns_of(1))
        elif "dsctable" in clazz:
            pass
        elif "wikitable" in clazz:
            pass
        elif "mainpagetable" in clazz:
            pass
        else:
            self.assertTrue(False, f"Unexpected table class: {clazz}")
        for assumption in assumptions:
            assumption(table)

    def assume_columns_of(self, num: int):
        def wrapper(table: HtmlElement):
            self.assertGreater(len(table), 0)
            ncols = sum([int(col.get("colspan", "1")) for col in table[0]])
            self.assertEqual(ncols, num, f"{table.get('class', '')} expects {num} columns, got {ncols}.")  # fmt: off

        return wrapper
