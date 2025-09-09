import itertools
import unittest
from typing import Callable

from lxml.etree import strip_tags
from lxml.html import HtmlElement, HTMLParser, fromstring

from cppref.core.cppreference.utils import Utils
from cppref.typing_ import Record
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
        from cppref.utils import Utils as Handler

        dbfile = self.get_root().joinpath("testdata", "index.db")
        records = Handler.query("cppreference", dbfile)
        from cppref.conf import ConfContext

        with ConfContext() as conf:
            root = conf.folder.joinpath("cppreference", "html")

        def toElement(record: Record) -> HtmlElement:
            doc = Handler.read_file(root.joinpath(f"{record.id}.html"))
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
                    self.assume(table)

    def assume(self, table: HtmlElement):
        strip_tags(table, "tbody")
        clazz = table.get("class", "")
        if len(table) == 0 or clazz == "" or len(table.text_content().strip()) == 0:
            return
        if "t-dcl-begin" in clazz:
            self._assume_columns_of(table, 3)
            self._assume_none_nested_table(table, 1, 2)
        elif "t-par-begin" in clazz:
            self._assume_columns_of(table, 3)
            self._assume_each_row(table, lambda row: len(row) < 2 or row[1].text_content().strip() == "-")  # fmt: off
            self._assume_none_nested_table(table, 0, 1)
        elif "t-dsc-begin" in clazz:
            self._assume_columns_of(table, 2)
            self._assume_none_nested_table(table, 0)
        elif "t-rev-begin" in clazz:
            self._assume_columns_of(table, 2)
            self._assume_none_nested_table(table, 1)
        elif "t-sdsc-begin" in clazz:
            for e in table.find_class("t-sdsc-sep"):
                parent = e.getparent()
                if parent is None:
                    self.assertTrue(False, "Expected a parent, got None")
                else:
                    self.assertEqual(len(parent), 1, "Expected t-sdsc-sep has no siblings")  # fmt: off
                    parent.drop_tree()
            self._assume_columns_of(table, 3)
            self._assume_none_nested_table(table, 1, 2)
        elif "eq-fun-cpp-table" in clazz:
            self._assume_columns_of(table, 1)
        elif "dsctable" in clazz:
            pass
        elif "wikitable" in clazz:
            pass
        elif "mainpagetable" in clazz:
            pass
        else:
            self.assertTrue(False, f"Unexpected table class: {clazz}")

    def _assume_columns_of(self, table: HtmlElement, num: int):
        self.assertGreater(len(table), 0)
        ncols = sum([int(col.get("colspan", "1")) for col in table[0]])
        self.assertEqual(ncols, num, f"{table.get('class', '')} expects {num} columns, got {ncols}.")  # fmt: off

    def _assume_each_row(self, table: HtmlElement, fn: Callable[[HtmlElement], bool]):
        self.assertTrue(all(map(fn, table)), table.text_content().strip())

    def _assume_none_nested_table(self, table: HtmlElement, *columns: int):
        for row in table:
            if any([col.get("colspan") is not None for col in row]):
                continue
            for e in itertools.chain(row[i] for i in columns):
                self.assertNotEqual(e.tag, "table")


class UtilTest(TestBase):
    def test_nested_table_width1(self):
        # from std::vector: https://en.cppreference.com/w/cpp/container/vector.html
        html_str = """\
<table class="t-par-begin">
   <tbody>
      <tr class="t-par">
         <td> T</td>
         <td> -</td>
         <td>
            The type of the elements.
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-until-cxx11">
                     <td><code>T</code> must meet the requirements of <a href="../named_req/CopyAssignable.html" title="cpp/named req/CopyAssignable"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">CopyAssignable</span></a> and <a href="../named_req/CopyConstructible.html" title="cpp/named req/CopyConstructible"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">CopyConstructible</span></a>.</td>
                     <td><span class="t-mark-rev t-until-cxx11">(until C++11)</span></td>
                  </tr>
                  <tr class="t-rev t-since-cxx11 t-until-cxx17">
                     <td>The requirements that are imposed on the elements depend on the actual operations performed on the container. Generally, it is required that element type is a complete type and meets the requirements of <a href="../named_req/Erasable.html" title="cpp/named req/Erasable"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">Erasable</span></a>, but many member functions impose stricter requirements.</td>
                     <td><span class="t-mark-rev t-since-cxx11">(since C++11)</span><br><span class="t-mark-rev t-until-cxx17">(until C++17)</span></td>
                  </tr>
                  <tr class="t-rev t-since-cxx17">
                     <td>
                        <p>The requirements that are imposed on the elements depend on the actual operations performed on the container. Generally, it is required that element type meets the requirements of <a href="../named_req/Erasable.html" title="cpp/named req/Erasable"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">Erasable</span></a>, but many member functions impose stricter requirements. This container (but not its members) can be instantiated with an incomplete element type if the allocator satisfies the <a href="../named_req/Allocator.html#Allocator_completeness_requirements" title="cpp/named req/Allocator">allocator completeness requirements</a>.</p>
                        <table class="wikitable ftm-begin">
                           <tbody>
                              <tr>
                                 <th><a href="../utility/feature_test.html" title="cpp/utility/feature test">Feature-test</a> macro</th>
                                 <th><abbr title="The year/month in which the feature was adopted. The hyperlink under each value opens a compiler support page with entry for given feature.">Value</abbr></th>
                                 <th><abbr title="Standard in which the feature is introduced; DR means defect report against that revision">Std</abbr></th>
                                 <th>Feature</th>
                              </tr>
                              <tr>
                                 <td><a href="../experimental/feature_test.html#cpp_lib_incomplete_container_elements" title="cpp/feature test"><code>__cpp_lib_incomplete_container_elements</code></a></td>
                                 <td><a href="../compiler_support/17.html#cpp_lib_incomplete_container_elements_201505L" title="cpp/compiler support/17"><code>201505L</code></a></td>
                                 <td><span class="t-mark">(C++17)</span></td>
                                 <td>Minimal incomplete type support</td>
                              </tr>
                           </tbody>
                        </table>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx17">(since C++17)</span></td>
                  </tr>
               </tbody>
            </table>
         </td>
      </tr>
      <tr class="t-par">
         <td> Allocator</td>
         <td> -</td>
         <td> An allocator that is used to acquire/release memory and to construct/destroy the elements in that memory. The type must meet the requirements of <a href="../named_req/Allocator.html" title="cpp/named req/Allocator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">Allocator</span></a>. <span class="t-rev-inl t-until-cxx20"><span>The behavior is undefined</span><span><span class="t-mark-rev t-until-cxx20">(until C++20)</span></span></span><span class="t-rev-inl t-since-cxx20"><span>The program is ill-formed</span><span><span class="t-mark-rev t-since-cxx20">(since C++20)</span></span></span> if <code>Allocator::value_type</code> is not the same as <code>T</code>.<span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/param_list_Allocator&amp;action=edit">[edit]</a></span></td>
      </tr>
   </tbody>
</table>"""
        html = fromstring(html_str, parser=HTMLParser(encoding="utf-8"))
        strip_tags(html, "tbody")
        self.assertEqual(Utils.nested_table_width(html), 6)

    def test_nested_table_width2(self):
        # from std::vector: https://en.cppreference.com/w/cpp/container/vector.html
        html_str = """\
<table class="t-dsc-begin">
   <tbody>
      <tr class="t-dsc-hitem">
         <td> Member type</td>
         <td> Definition</td>
      </tr>
      <tr class="t-dsc">
         <td> <code>value_type</code></td>
         <td> <code>T</code><span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_value_type&amp;action=edit">[edit]</a></span></td>
      </tr>
      <tr class="t-dsc">
         <td> <code>allocator_type</code></td>
         <td> <code>Allocator</code><span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_allocator_type&amp;action=edit">[edit]</a></span></td>
      </tr>
      <tr class="t-dsc">
         <td> <code>size_type</code></td>
         <td> Unsigned integer type (usually <span class="t-lc"><a href="../types/size_t.html" title="cpp/types/size t">std::size_t</a></span>)<span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_size_type&amp;action=edit">[edit]</a></span></td>
      </tr>
      <tr class="t-dsc">
         <td> <code>difference_type</code></td>
         <td> Signed integer type (usually <span class="t-lc"><a href="../types/ptrdiff_t.html" title="cpp/types/ptrdiff t">std::ptrdiff_t</a></span>)<span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_difference_type&amp;action=edit">[edit]</a></span></td>
      </tr>
      <tr class="t-dsc">
         <td> <code>reference</code></td>
         <td> <span class="mw-geshi cpp source-cpp">value_type<span class="sy3">&amp;</span></span><span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_reference&amp;action=edit">[edit]</a></span></td>
      </tr>
      <tr class="t-dsc">
         <td> <code>const_reference</code></td>
         <td> <span class="mw-geshi cpp source-cpp"><span class="kw4">const</span> value_type<span class="sy3">&amp;</span></span><span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_const_reference&amp;action=edit">[edit]</a></span></td>
      </tr>
      <tr class="t-dsc">
         <td> <code>pointer</code></td>
         <td>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-until-cxx11">
                     <td>
                        <p><code>Allocator::pointer</code></p>
                     </td>
                     <td><span class="t-mark-rev t-until-cxx11">(until C++11)</span></td>
                  </tr>
                  <tr class="t-rev t-since-cxx11">
                     <td>
                        <p><span class="mw-geshi cpp source-cpp"><a href="../memory/allocator_traits.html"><span class="kw706">std::<span class="me2">allocator_traits</span></span></a><span class="sy1">&lt;</span>Allocator<span class="sy1">&gt;</span><span class="sy4">::</span><span class="me2">pointer</span></span></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx11">(since C++11)</span></td>
                  </tr>
               </tbody>
            </table>
            <span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_pointer&amp;action=edit">[edit]</a></span>
         </td>
      </tr>
      <tr class="t-dsc">
         <td> <code>const_pointer</code></td>
         <td>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-until-cxx11">
                     <td>
                        <p><code>Allocator::const_pointer</code></p>
                     </td>
                     <td><span class="t-mark-rev t-until-cxx11">(until C++11)</span></td>
                  </tr>
                  <tr class="t-rev t-since-cxx11">
                     <td>
                        <p><span class="mw-geshi cpp source-cpp"><a href="../memory/allocator_traits.html"><span class="kw706">std::<span class="me2">allocator_traits</span></span></a><span class="sy1">&lt;</span>Allocator<span class="sy1">&gt;</span><span class="sy4">::</span><span class="me2">const_pointer</span></span></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx11">(since C++11)</span></td>
                  </tr>
               </tbody>
            </table>
            <span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_const_pointer&amp;action=edit">[edit]</a></span>
         </td>
      </tr>
      <tr class="t-dsc">
         <td> <code>iterator</code></td>
         <td>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-until-cxx20">
                     <td>
                        <p><a href="../named_req/RandomAccessIterator.html" title="cpp/named req/RandomAccessIterator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">LegacyRandomAccessIterator</span></a> and <a href="../named_req/ContiguousIterator.html" title="cpp/named req/ContiguousIterator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">LegacyContiguousIterator</span></a> to <code>value_type</code></p>
                     </td>
                     <td><span class="t-mark-rev t-until-cxx20">(until C++20)</span></td>
                  </tr>
                  <tr class="t-rev t-since-cxx20">
                     <td>
                        <p><a href="../named_req/RandomAccessIterator.html" title="cpp/named req/RandomAccessIterator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">LegacyRandomAccessIterator</span></a>, <a href="../iterator/contiguous_iterator.html" title="cpp/iterator/contiguous iterator"><code>contiguous_iterator</code></a>, and <a href="../named_req/ConstexprIterator.html" title="cpp/named req/ConstexprIterator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">ConstexprIterator</span></a> to <code>value_type</code></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx20">(since C++20)</span></td>
                  </tr>
               </tbody>
            </table>
            <span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_iterator&amp;action=edit">[edit]</a></span>
         </td>
      </tr>
      <tr class="t-dsc">
         <td> <code>const_iterator</code></td>
         <td>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-until-cxx20">
                     <td>
                        <p><a href="../named_req/RandomAccessIterator.html" title="cpp/named req/RandomAccessIterator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">LegacyRandomAccessIterator</span></a> and <a href="../named_req/ContiguousIterator.html" title="cpp/named req/ContiguousIterator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">LegacyContiguousIterator</span></a> to <span class="mw-geshi cpp source-cpp"><span class="kw4">const</span> value_type</span></p>
                     </td>
                     <td><span class="t-mark-rev t-until-cxx20">(until C++20)</span></td>
                  </tr>
                  <tr class="t-rev t-since-cxx20">
                     <td>
                        <p><a href="../named_req/RandomAccessIterator.html" title="cpp/named req/RandomAccessIterator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">LegacyRandomAccessIterator</span></a>, <a href="../iterator/contiguous_iterator.html" title="cpp/iterator/contiguous iterator"><code>contiguous_iterator</code></a>, and <a href="../named_req/ConstexprIterator.html" title="cpp/named req/ConstexprIterator"><span style="font-family: Georgia, 'DejaVu Serif', serif; font-style:italic">ConstexprIterator</span></a> to <span class="mw-geshi cpp source-cpp"><span class="kw4">const</span> value_type</span></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx20">(since C++20)</span></td>
                  </tr>
               </tbody>
            </table>
            <span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_const_iterator&amp;action=edit">[edit]</a></span>
         </td>
      </tr>
      <tr class="t-dsc">
         <td> <code>reverse_iterator</code></td>
         <td> <span class="mw-geshi cpp source-cpp"><a href="../iterator/reverse_iterator.html"><span class="kw664">std::<span class="me2">reverse_iterator</span></span></a><span class="sy1">&lt;</span>iterator<span class="sy1">&gt;</span></span><span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_reverse_iterator&amp;action=edit">[edit]</a></span></td>
      </tr>
      <tr class="t-dsc">
         <td> <code>const_reverse_iterator</code></td>
         <td> <span class="mw-geshi cpp source-cpp"><a href="../iterator/reverse_iterator.html"><span class="kw664">std::<span class="me2">reverse_iterator</span></span></a><span class="sy1">&lt;</span>const_iterator<span class="sy1">&gt;</span></span><span class="editsection noprint plainlinks" title="Edit this template"><a rel="nofollow" class="external text" href="https://en.cppreference.com/mwiki/index.php?title=Template:cpp/container/dsc_const_reverse_iterator&amp;action=edit">[edit]</a></span></td>
      </tr>
   </tbody>
</table>"""
        html = fromstring(html_str, parser=HTMLParser(encoding="utf-8"))
        strip_tags(html, "tbody")
        self.assertEqual(Utils.nested_table_width(html), 3)

    def test_nested_table_width3(self):
        # from List-initialization https://en.cppreference.com/w/cpp/language/list_initialization.html
        html_str = """\
<table class="t-sdsc-begin">
   <tbody>
      <tr>
         <td colspan="10" class="t-sdsc-sep"></td>
      </tr>
      <tr class="t-sdsc">
         <td>
            <span class="t-spar">T object</span> <code><b>{</b></code> <span class="t-spar">arg1, arg2, ...</span> <code><b>};</b></code>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-since-cxx20">
                     <td>
                        <p><span class="t-spar">T object</span><code><b>{.</b></code><span class="t-spar">des1</span> <code><b>=</b></code> <span class="t-spar">arg1</span> <code><b>, .</b></code><span class="t-spar">des2</span> <code><b>{</b></code> <span class="t-spar">arg2</span> <code><b>}</b></code> <span class="t-spar">...</span> <code><b>};</b></code></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx20">(since C++20)</span></td>
                  </tr>
               </tbody>
            </table>
         </td>
         <td> (1)</td>
         <td class="t-sdsc-nopad"></td>
      </tr>
      <tr>
         <td colspan="10" class="t-sdsc-sep"></td>
      </tr>
      <tr class="t-sdsc">
         <td>
            <span class="t-spar">T</span> <code><b>{</b></code> <span class="t-spar">arg1, arg2, ...</span> <code><b>}</b></code>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-since-cxx20">
                     <td>
                        <p><span class="t-spar">T</span> <code><b>{.</b></code><span class="t-spar">des1</span> <code><b>=</b></code> <span class="t-spar">arg1</span> <code><b>, .</b></code><span class="t-spar">des2</span> <code><b>{</b></code> <span class="t-spar">arg2</span> <code><b>}</b></code> <span class="t-spar">...</span> <code><b>}</b></code></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx20">(since C++20)</span></td>
                  </tr>
               </tbody>
            </table>
         </td>
         <td> (2)</td>
         <td class="t-sdsc-nopad"></td>
      </tr>
      <tr>
         <td colspan="10" class="t-sdsc-sep"></td>
      </tr>
      <tr class="t-sdsc">
         <td>
            <code><b>new</b></code> <span class="t-spar">T</span> <code><b>{</b></code> <span class="t-spar">arg1, arg2, ...</span> <code><b>}</b></code>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-since-cxx20">
                     <td>
                        <p><code><b>new</b></code> <span class="t-spar">T</span> <code><b>{.</b></code><span class="t-spar">des1</span> <code><b>=</b></code> <span class="t-spar">arg1</span> <code><b>, .</b></code><span class="t-spar">des2</span> <code><b>{</b></code> <span class="t-spar">arg2</span> <code><b>}</b></code> <span class="t-spar">...</span> <code><b>}</b></code></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx20">(since C++20)</span></td>
                  </tr>
               </tbody>
            </table>
         </td>
         <td> (3)</td>
         <td class="t-sdsc-nopad"></td>
      </tr>
      <tr>
         <td colspan="10" class="t-sdsc-sep"></td>
      </tr>
      <tr class="t-sdsc">
         <td>
            <span class="t-spar">Class</span> <code><b>{</b></code> <span class="t-spar">T member</span> <code><b>{</b></code> <span class="t-spar">arg1, arg2, ...</span> <code><b>}; };</b></code>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-since-cxx20">
                     <td>
                        <p><span class="t-spar">Class</span> <code><b>{</b></code> <span class="t-spar">T member</span> <code><b>{.</b></code><span class="t-spar">des1</span> <code><b>=</b></code> <span class="t-spar">arg1</span> <code><b>, .</b></code><span class="t-spar">des2</span> <code><b>{</b></code> <span class="t-spar">arg2</span> <code><b>}</b></code> <span class="t-spar">...</span> <code><b>}; };</b></code></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx20">(since C++20)</span></td>
                  </tr>
               </tbody>
            </table>
         </td>
         <td> (4)</td>
         <td class="t-sdsc-nopad"></td>
      </tr>
      <tr>
         <td colspan="10" class="t-sdsc-sep"></td>
      </tr>
      <tr class="t-sdsc">
         <td>
            <span class="t-spar">Class</span><code><b>::</b></code><span class="t-spar">Class</span><code><b>()&nbsp;:</b></code> <span class="t-spar">member</span> <code><b>{</b></code> <span class="t-spar">arg1, arg2, ...</span> <code><b>} {...</b></code>
            <table class="t-rev-begin">
               <tbody>
                  <tr class="t-rev t-since-cxx20">
                     <td>
                        <p><span class="t-spar">Class</span><code><b>::</b></code><span class="t-spar">Class</span><code><b>()&nbsp;:</b></code> <span class="t-spar">member</span> <code><b>{.</b></code><span class="t-spar">des1</span> <code><b>=</b></code> <span class="t-spar">arg1</span> <code><b>, .</b></code><span class="t-spar">des2</span> <code><b>{</b></code> <span class="t-spar">arg2</span> <code><b>}</b></code> <span class="t-spar">...</span><code><b>} {...</b></code></p>
                     </td>
                     <td><span class="t-mark-rev t-since-cxx20">(since C++20)</span></td>
                  </tr>
               </tbody>
            </table>
         </td>
         <td> (5)</td>
         <td class="t-sdsc-nopad"></td>
      </tr>
      <tr>
         <td colspan="10" class="t-sdsc-sep"></td>
      </tr>
   </tbody>
</table>"""
        html = fromstring(html_str, parser=HTMLParser(encoding="utf-8"))
        strip_tags(html, "tbody")
        self.assertEqual(Utils.nested_table_width(html), 3)
