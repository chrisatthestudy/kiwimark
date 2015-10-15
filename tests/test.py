#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
KiwiMarkup Test Unit

Run using 'python test.py'
"""

# Standard library imports

import imp
import re

# Application specific imports

# Because Kiwimark is not installed into the Python library we need to load it
# manually.
scriptfile, pathname, description = imp.find_module("kiwimark", ["../kiwimark"])
try:
    kiwimark = imp.load_module("kiwimark", scriptfile, pathname, description)
finally:
    scriptfile.close()

if (__name__ == "__main__"):

    # Basic unit tests
    import unittest

    class KiwiMarkupCase(unittest.TestCase):

        def setUp(self):
            self.api = kiwimark.KiwiMarkup()

        def tearDown(self):
            self.api = None

        def testBasic(self):
            """ Verify that the instance was created """
            self.assertNotEqual(self.api, None)

        def testExecute(self):
            """ Verify the main execution method """
            self.assertNotEqual(self.api.execute("# Test Number 1"), 0)

        def testHeaderRegex(self):
            """
            Regex for SETEXT style headers, starting (after up to three
            whitespace characters) with a row of up to six '#' characters. The
            header text can also be followed by additional '#' characters up
            to the end of the line -- these will be omitted from the output.
            """
            regex = kiwimark.HEADER_REGEX = r"^[\s]{0,3}([#]{1,6})[\s]*([^#]*)"

            # No match
            m = re.search(regex, "There is no header markup here")
            self.assertEqual(m, None)

            # Simple match for Header 1
            m = re.search(regex, "# Header 1")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), "#")
            self.assertEqual(m.group(2), "Header 1")

            # Match for Header 3
            m = re.search(regex, "### Header 3")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), "###")
            self.assertEqual(m.group(2), "Header 3")

        def testListRegex(self):
            """
            Regex for list items, optionally indented by whitespace, and
            indicated by a single asterisk followed by whitespace and then
            the actual text of the item.
            """
            regex = kiwimark.LIST_REGEX = r"^([\s]*)[\*][\s]+(.*)"

            # No match
            m = re.search(regex, "There is no list markup here")
            self.assertEqual(m, None)

            # Simple match for list entry
            m = re.search(regex, "* List entry")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), "")
            self.assertEqual(m.group(2), "List entry")

            # Match including white-space
            m = re.search(regex, "    * List entry")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), "    ")
            self.assertEqual(m.group(2), "List entry")

        def testTableHeaderRegex(self):
            """
            Regex for table headers, which consist of a row of '-' characters
            split up by one or more '|' characters or '+' characters.
            """
            regex = kiwimark.TABLE_HEADER_REGEX = r"^[\s]{0,3}(\||\+)*((-{3,})(\||\+))+"

            # No match
            m = re.search(regex, "There is no table header markup here")
            self.assertEqual(m, None)

            # Match with "|" separators
            m = re.search(regex, "---|---|---")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), None)
            self.assertEqual(m.group(2), "---|")

            # Match with "+" separators
            m = re.search(regex, "---+---+---")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), None)
            self.assertEqual(m.group(2), "---+")

        def testBoldStartRegex(self):
            """
            Regex for start of bold text
            """
            regex = kiwimark.BOLD_START_REGEX = r"(^|\s)(\*\*)([^\s])"

            # No match
            m = re.search(regex, "There is no bold markup here")
            self.assertEqual(m, None)

            # Simple match
            m = re.search(regex, "**Some bold** text.")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.groups(2), ("", "**", "S"))

        def testBoldEndRegex(self):
            """
            Regex for end of bold text
            """
            regex = kiwimark.BOLD_END_REGEX = r"([^\s])(\*\*)([\):;.,?\s]+|$)"

            # No match
            m = re.search(regex, "There is no bold markup here")
            self.assertEqual(m, None)

            # Simple match
            m = re.search(regex, "**Some bold** text.")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.groups(2), ("d", "**", " "))

        def testEmphStartRegex(self):
            """
            Regex for start of emphasized text
            """
            regex = kiwimark.EMPH_START_REGEX = r"(^|\s)(_)([^\s])"

            # No match
            m = re.search(regex, "There is no emphasized markup here")
            self.assertEqual(m, None)

            # Simple match
            m = re.search(regex, "Some _emphasized_ text.")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.groups(2), (" ", "_", "e"))

        def testEmphEndRegex(self):
            """
            Regex for end of emphasized text
            """
            regex = kiwimark.EMPH_END_REGEX = r"([^\s])(_)([\):;.,?\s]+|$)"

            # No match
            m = re.search(regex, "There is no emphasized markup here")
            self.assertEqual(m, None)

            # Simple match
            m = re.search(regex, "Some text which has been _emphasized_.")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.groups(2), ("d", "_", "."))

            # Must ignore in-word underscores
            m = re.search(regex, "There is no emphasized mark_up here")
            self.assertEqual(m, None)

        def testURLRegex(self):
            """
            Regex for Markdown-style URL mark-up: [title-text](path/to/url).

            This doesn't check for valid URL -- there are too many options.
            """
            regex = kiwimark.URL_REGEX = r"\[([^]]*)\]\(([^\)]*)\)"

            # No match
            m = re.search(regex, "There is no URL markup here")
            self.assertEqual(m, None)

            # Simple match
            m = re.search(regex, "Here is a [link](www.link.com) to a website.")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.groups(1), ("link", "www.link.com"))

        def testMarkdownImgRegex(self):
            """
            Regex for Markdown-style image mark-up: ![alt-text](path/to/image.png)
            """
            regex = kiwimark.MD_IMG_REGEX = r"!\[([^]]*)\]\(([^\)]*)\)"

            # No match
            m = re.search(regex, "There is no image markup here")
            self.assertEqual(m, None)

            # Simple match
            m = re.search(regex, "Here is a ![picture](/path/image.png) of something.")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.groups(1), ("picture", "/path/image.png"))

        def testImgRegex(self):
            """ Verify  the img markup regular expression """
            regex = kiwimark.IMG_REGEX

            # No match
            m = re.search(regex, "There is no img markup here")
            self.assertEqual(m, None)

            # Simple match
            m = re.search(regex, '[img](graphics/test.png)')
            self.assertNotEqual(len(m.groups()), 0)

            # Match with CSS class
            m = re.search(regex, '[img.left](graphics/test.png)')
            self.assertEqual(m.group(3), 'left')

            # Match with alt text
            m = re.search(regex, '[img:alt](graphics/test.png)')
            self.assertEqual(m.group(6), 'alt')

            # Match with CSS class and alt text
            m = re.search(regex, '[img.left:alt](graphics/test.png)')
            self.assertEqual(m.group(3), 'left')
            self.assertEqual(m.group(6), 'alt')

            # Return the expected line
            line = "[img.left:alt](graphics/test.png)"
            expected_result = "<img src='graphics/test.png' class='left' alt='alt' title='alt'/>"
            line = self.api.re_sub(self.api.imgPattern, r"<img src='\7' class='\3' alt='\6' title='\6'/>", line)
            self.assertEqual(line, expected_result)

        def testFootnoteRegex(self):
            """
            FOOTNOTE_REGEX for footnotes (links to footnote_nn)
            """
            regex = kiwimark.FOOTNOTE_REGEX = r"\[\^([0-9]+)\]"

            # No match
            m = re.search(regex, "There is no footnote here")
            self.assertEqual(m, None)

            m = re.search(regex, "See the footnote[^1] below")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), "1")

        def testFootnoteTargetRegex(self):
            """
            FOOTNOTE_TARGET_REGEX for footnote targets (links to footnote_ref_nn)
            """
            regex = kiwimark.FOOTNOTE_TARGET_REGEX = r"\[\^([0-9]+)\]:"

            # No match
            m = re.search(regex, "There is no footnote here")
            self.assertEqual(m, None)

            m = re.search(regex, "[^1]: Some additional info")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), "1")

        def testCodeBlockStartRegex(self):
            regex = kiwimark.CODEBLOCK_START_REGEX

            # No match
            m = re.search(regex, "There is no code: marker here")
            self.assertEqual(m, None)

            # Simple match
            m = re.search(regex, "code:\n")
            self.assertNotEqual(len(m.groups()), 0)

            # Match with language specified
            m = re.search(regex, "code:javascript\n")
            self.assertNotEqual(len(m.groups()), 0)
            self.assertEqual(m.group(1), "javascript")

        def testCodeBlockEndRegex(self):
            regex = kiwimark.CODEBLOCK_END_REGEX

            # No match
            m = re.search(regex, "There is no :code marker here")

            # Simple match
            m = re.search(regex, ":code\n")
            self.assertNotEqual(m, None)
            
    unittest.main()


