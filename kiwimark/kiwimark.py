#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Kiwi Markup

This script implements the mark-up for the Kiwi system (essentially a
static website generator). It expects to be given a list of text lines
which it converts to the equivalent HTML format.

Because this is the first part of a larger system it is not really
intended to be run stand-alone, but see the "if __name___..." section
at the end of the script for simple command-line use.

See README.md for more details
"""

import sys
import re
import cgi

KIWI_MODE_STD = 0
KIWI_MODE_ORG = 1

# Regex definitions ("Now you have two problems...")

# Regex for SETEXT style headers, starting (after up to three
# whitespace characters) with a row of up to six '#' characters. The
# header text can also be followed by additional '#' characters up
# to the end of the line -- these will be omitted from the output.
HEADER_REGEX = r"^[\s]{0,3}([#]{1,6})[\s]*([^#]*)"

# Regex for list items, optionally indented by whitespace, and
# indicated by a single asterisk followed by whitespace and then
# the actual text of the item.
LIST_REGEX = r"^([\s]*)[\*][\s]+(.*)"

# Regex for table headers, which consist of a row of '-' characters
# split up by one or more '|' characters or '+' characters.
TABLE_HEADER_REGEX = r"^[\s]{0,3}(\||\+)*((-{3,})(\||\+))+"

# Regexes for bold and emphasized text
BOLD_START_REGEX = r"(^|[\[\]\s]| _)(\*\*)([^\s])"
BOLD_END_REGEX = r"([^\s])(\*\*)(_ |[\):;.,?\[\]\s]+|$)"
EMPH_START_REGEX = r"(^|[\[\]\s\"]|<b>)(_)([^\s])"
EMPH_END_REGEX = r"([^\s])(_)(<\/b>|[\):;.,?\"\[\]\s]+|$)"

# Regex for Markdown-style URL mark-up: [title-text](path/to/url)
MD_URL_REGEX = r"\[([^]]*)\]\(([^\)]*)\)"

# Regex for org-mode URL mark-up: [[path/to/url][title-text]]
ORG_URL_REGEX = r"\[\[([^]]*)\]\[([^]]*)\]\]"

# Regex for Markdown-style image mark-up: ![alt-text](path/to/image.png)
MD_IMG_REGEX = r"!\[([^]]*)\]\(([^\)]*)\)"

# IMG_REGEX matches: [img.class-name:alt-text](path/to/image.png) where the
# class-name and alt-text elements are optional, but the regex will return
# empty groups if either of them is missing. Note that this regex is very
# clumsy, but it returns the class name in group 3, the alt-text in group 6,
# and the file path in group 7. If the class name or the alt-text are
# empty, the groups will still exist (as groups 3 and 6) but will be
# empty.
IMG_REGEX = r"\[img(()|\.([^\]:]*))(()|:([^\]]*))\]\(([^\)]*)\)"

# AUDIO_REGEX matches: [audio.class-name:alt-text](path/to/image.png) where the
# class-name and alt-text elements are optional, but the regex will return
# empty groups if either of them is missing (see the IMG_REGEX above for
# additional details about the groups).
AUDIO_REGEX = r"\[audio(()|\.([^\]:]*))(()|:([^\]]*))\]\(([^\)]*)\)"

# LINK_REGEX matches: [link.class-name:alt-text](path/to/link) where the
# class-name and alt-text elements are optional, but the regex will return
# empty groups if either of them is missing (see the IMG_REGEX above for
# additional details about the groups).
LINK_REGEX = r"\[link(()|\.([^\]:]*))(()|:([^\]]*))\]\(([^\)]*)\)"

# FOOTNOTE_REGEX for footnotes (links to footnote_nn)
FOOTNOTE_REGEX = r"\[\^([0-9]+)\]"

# FOOTNOTE_TARGET_REGEX for footnote targets (links to footnote_ref_nn)
FOOTNOTE_TARGET_REGEX = r"\[\^([0-9]+)\]:"

# CODEBLOCK_START_REGEX finds the beginning of a block of text that should
# be formatted as code. The marker can optionally include a language
# name after the 'code:' marker, but should otherwise be on a line on its
# own.
CODEBLOCK_START_REGEX = r"^[\s]*code:([^\s]*)[\s]*$"

# CODEBLOCK_END_REGEX finds the marker for the end of a block of text
# that should be formatted as code. The marker should be on a line on its
# own.
CODEBLOCK_END_REGEX = r"^[\s]*:code[\s]*$"

class KiwiMarkup:
    """
    Main processing class. Call the execute() method to process a list of
    text lines. On return, the KiwiMarkup.output variable will hold a list
    of lines in HTML format. Note that this is an HTML fragment, and does
    not include any framing <HTML> and <BODY> tags -- it is assumed that
    the calling program will take the output and insert it into an appropriate
    template.
    """

    def __init__(self):
        self.state  = KiwiState()
        self.boldStartPattern = re.compile(BOLD_START_REGEX)
        self.boldEndPattern = re.compile(BOLD_END_REGEX)
        self.emphStartPattern = re.compile(EMPH_START_REGEX)
        self.emphEndPattern = re.compile(EMPH_END_REGEX)
        self.mdUrlPattern = re.compile(MD_URL_REGEX)
        self.orgmodeUrlPattern = re.compile(ORG_URL_REGEX)
        self.mdImgPattern = re.compile(MD_IMG_REGEX)
        self.imgPattern = re.compile(IMG_REGEX)
        self.audioPattern = re.compile(AUDIO_REGEX)
        self.linkPattern = re.compile(LINK_REGEX)
        self.footnotePattern = re.compile(FOOTNOTE_REGEX)
        self.footnoteTargetPattern = re.compile(FOOTNOTE_TARGET_REGEX)

    def execute(self, lines, mode = None):
        """
        Main entry point. The lines parameter should be a list of
        the plain text lines which are to be converted to HTML,
        and mode indicates the actual processing required -- the
        default is KIWI_MODE_STD.
        """
        assert (lines), "No lines provided for processing"
        if (mode == None):
            mode = KIWI_MODE_STD
            if len(lines) > 0:
                # Check the first line to see if this is an
                # org-mode file, and if it is, override the
                # mode.
                if re.search("-*- mode: org -*-", lines[0]):
                    mode = KIWI_MODE_ORG

        self.mode = mode
        self.line = KiwiLineScanner(self.mode)
        self.thisLine = None
        self.nextLine = None
        self.indents = []
        self.output = []

        # Process the lines
        for line in lines:
            # The processing often needs to know the contents of the next
            # line, so we read one line ahead. Therefore thisLine is
            # actually the line we read previously (and will be None on the
            # very first cycle of this loop)
            self.thisLine = self.nextLine

            # Convert tabs to spaces
            self.nextLine = re.sub("\t", "    ", line.rstrip())

            if not self.line.skipNextLine:
                self.processLine()
            else:
                # Never skip more than one line
                self.line.skipNextLine = False

        # Process the final line
        if not self.line.skipNextLine:
            self.thisLine = self.nextLine
            self.nextLine = ""
            self.processLine()

        self.endAllSections()

        return len(self.output) > 0

    def startParagraph(self):
        """
        Starts a new <p> section, provided there is not one already open.
        """
        if not self.state.inParagraph:
            self.output.append('<p>')
            self.state.inParagraph = True

    def endParagraph(self):
        """
        Ends a current <p> section. If no paragraph is open, does nothing.
        """
        if self.state.inParagraph:
            self.output.append('</p>')
            self.state.inParagraph = False

    def startBlock(self):
        """
        Starts a new 'PRE' block, provided there is no block open. Does nothing
        if the block is already open.
        """
        if not self.state.inBlock:
            self.output.append('<pre>')
            self.state.inBlock = True

    def endBlock(self):
        """
        Ends any current 'PRE' block. If no block is open, does nothing.
        """
        if self.state.inBlock:
            self.output.append('</pre>')
            self.state.inBlock = False

    def listIndent(self, increment = 0):
        """
        Returns a string of spaces to indent a list item, based on the current
        number of sub-lists that are open. Note that this is purely to apply
        'pretty' formatting to the HTML code, and has no other effect.

        The 'increment' parameter allows items to be indented on step further,
        so that LI tags can be indented more deeply than the UL tags
        """
        return "    " * (len(self.indents) - 1 + increment)

    def startList(self):
        """
        Starts a new unordered list ('<UL>'). If one is already open,
        and the current line is more deeply indented than the list
        is at present, starts a new sub-list. If the current line is
        indented by less than the list, ends the current sub-list.
        """
        nested = False
        if len(self.indents) > 0:
            # Get the last indentation level, and if the
            # current line is indented by a greater amount
            # we have to start a sub-list. If it is
            # indented by a lesser amount, we have to
            # end the current sub-list.
            indent = self.indents[-1]
            if self.line.listIndent > indent:
                nested = True
            elif self.line.listIndent < indent:
                self.endNestedList()
        if nested or not self.state.inList:
            # Save the indentation level
            self.indents.append(self.line.listIndent)
            self.endParagraph()

            # If a sub-list is being started, indent the tag
            # by an extra amount
            if nested:
                self.output.append('%s<ul>' % self.listIndent(1))
            else:
                self.output.append('%s<ul>' % self.listIndent())
            self.state.inList = True

    def endNestedList(self):
        """
        Ends a sublist if one is open. This should only be called directly
        from endList() below.
        """
        if len(self.indents) > 0:
            indent = self.indents[-1]
            if self.line.listIndent < indent:
                # Close the list and the LI tag
                self.output.append('%s</ul>' % self.listIndent(1))
                self.output.append('%s</li>' % self.listIndent())
                self.indents.pop()
                # It's possible that the current line is actually
                # ending more than one list, so recursively call
                # call this method again to check.
                self.endNestedList()

    def endList(self):
        """
        Ends the current list, if any. If the current list is a sublist,
        this ends the sublist, and only closes the list completely if
        there are no more sublists.
        """
        if self.state.inList:
            if len(self.indents) > 0:
                self.endNestedList()
            if len(self.indents) == 0:
                self.output.append('%s</ul>' % self.listIndent())
                self.state.inList = False

    def endAllLists(self):
        """
        Forces any sublists to be closed, and also closes the main
        list, if any.
        """
        while len(self.indents) > 0:
            self.output.append('%s</ul>' % self.listIndent(1))
            self.output.append('%s</li>' % self.listIndent())
            self.indents.pop()
        self.endList()

    def startTable(self):
        """
        Starts a new table ('<TABLE>'). If one is already open, does nothing.
        """
        if not self.state.inTable:
            self.output.append('<table>')
            self.state.inTable = True

    def endTable(self):
        """
        Ends any open table. If no table is open, does nothing.
        """
        if self.state.inTable:
            self.output.append('</table>')
            self.state.inTable = False

    def startOrgSection(self):
        """
        Starts a set of org-mode headers. A group of org-mode headers
        which are not separated by blank lines will be gathered under
        one '<p>' tag, separated by line-break ('<br>') tags.
        """
        if not self.state.inOrgSection:
            self.output.append('<p>')
            self.state.inOrgSection = True

    def endOrgSection(self):
        """
        Ends any open org-header section. If no section is open, does nothing.
        """
        if self.state.inOrgSection:
            self.output.append('</p>')
            self.state.inOrgSection = False

    def startCodeSection(self):
        """
        Starts a block of text that should be formatted as code
        """
        if not self.state.inCodeSection:
            self.output.append('<pre>')
            self.output.append('<code>')
            self.state.inCodeSection = True

    def endCodeSection(self):
        """
        Ends a block of code
        """
        if self.state.inCodeSection:
            self.output.append('</code>')
            self.output.append('</pre>')
            self.state.inCodeSection = False
            
    def endAllSections(self):
        """
        Closes any/all open tags
        """
        self.endOrgSection()
        self.endBlock()
        self.endAllLists()
        self.endTable()
        self.endParagraph()

    def addListLine(self):
        """
        Adds a new list item, starting a new list if necessary.
        """
        self.startList()

        if self.line.isNestedList:
            # For sub-lists the HTML spec requires that we leave the LI tag open
            self.thisLine = "%s<li>%s" % (self.listIndent(1), self.line.listText)
        else:
            self.thisLine = "%s<li>%s</li>" % (self.listIndent(1), self.line.listText)

    def imgAttributes(self, line):
        """
        Extracts any attributes from a line containing img markup
        """
        attributes = re.search(IMG_REGEX, line)
        if (attributes):
            return (attributes.group(1)[1:], attributes.group(3)[1:])
        else:
            return None

    def re_sub(self, pattern, replacement, string):
        """
        Work-around for re.sub unmatched group error.

        Note that an alternative would be to use the regex package, but this
        is not a default part of the Python library, and I want to avoid
        external dependencies if at all possible.

        See https://gist.github.com/gromgull/3922244
        """
        def _r(m):
            # Now this is ugly.
            # Python has a "feature" where unmatched groups return None
            # then re.sub chokes on this.
            # see http://bugs.python.org/issue1519638

            # this works around and hooks into the internal of the re module...

            # the match object is replaced with a wrapper that
            # returns "" instead of None for unmatched groups

            class _m():
                def __init__(self, m):
                    self.m=m
                    self.string=m.string
                def group(self, n):
                    return m.group(n) or ""

            return re._expand(pattern, _m(m), replacement)

        return re.sub(pattern, _r, string)

    def applyInlineMarkup(self, line):
        """
        Applies markup to the supplied line and returns the results. It
        assumes the self.line holds the additional details for the line.
        """
        if not self.line.isOrgHeader:
            line = self.boldStartPattern.sub(r"\1<b>\3", line)
            line = self.boldEndPattern.sub(r"\1</b>\3", line)
        line = self.emphStartPattern.sub(r"\1<i>\3", line)
        line = self.emphEndPattern.sub(r"\1</i>\3", line)
        line = self.mdImgPattern.sub(r"<img src='\2' alt='\1' title='\1'/>", line)
        line = self.re_sub(self.imgPattern, r"<img src='\7' class='\3' alt='\6' title='\6'/>", line)
        line = self.re_sub(self.audioPattern, r"<audio width='300px' height='32px' src='\7' class='\3' controls='controls'> Your browser does not support audio playback. </audio>", line)
        line = self.re_sub(self.linkPattern, r"<a href='\7' class='\3' alt='\6'>\6</a>", line)
        line = self.mdUrlPattern.sub(r"<a href='\2'>\1</a>", line)
        line = self.orgmodeUrlPattern.sub(r"<a href='\1'>\2</a>", line)
        line = self.footnoteTargetPattern.sub(r"\1. <a name='footnote_target_\1' href='#footnote_ref_\1'>&#160;&#8617;</a>", line)
        line = self.footnotePattern.sub(r"<a name='footnote_ref_\1' href='#footnote_target_\1'>[<sup>\1</sup>]</a>", line)
        return line
        
    def processLine(self):
        """
        Processes the current line, converting it into the appropriate
        HTML.
        """
        includeLine = True;
        if (self.thisLine != None):
            # Scan the line to get the details for it, then carry out the
            # appropriate actions, based on the line type
            self.line.scan(self.thisLine, self.nextLine, self.state)

            if self.mode == KIWI_MODE_ORG and self.line.isOrgHeader:
                self.startOrgSection()
                self.thisLine = "%s<br/>" % self.thisLine

            elif self.line.isCodeStart:
                self.endAllSections()
                self.startCodeSection()
                includeLine = False

            elif self.line.isCodeEnd:
                self.endCodeSection()
                includeLine = False
                
            elif self.state.inCodeSection:
                # If we are in a code section, we don't want to do any
                # other processing of the line
                pass
            
            elif self.line.isList:
                self.endOrgSection()
                self.endBlock()
                self.endTable()
                self.endParagraph()
                self.addListLine()

            elif self.line.isBlock:
                self.endOrgSection()
                self.endAllLists()
                self.endTable()
                self.endParagraph()
                self.startBlock()

            elif self.line.isTable:
                self.endOrgSection()
                self.endBlock()
                self.endAllLists()
                self.endParagraph()
                self.startTable()
                self.output.append("    <tr>")
                for column in self.line.tableColumns:
                    column = self.applyInlineMarkup(column)
                    if self.line.isTableHeader:
                        self.output.append("        <th>%s</th>" % column)
                    else:
                        self.output.append("        <td>%s</td>" % column)
                self.output.append("    </tr>")
                includeLine = False

            elif self.line.isHeader:
                self.endAllSections()
                self.thisLine = "<h%d>%s</h%d>" %(self.line.headerLevel, self.line.headerText, self.line.headerLevel)

            elif self.line.isHorizontalLine:
                self.endAllSections()
                self.thisLine = "<hr>"

            elif self.line.isParagraph:
                self.endOrgSection()
                self.endBlock()
                self.endAllLists()
                self.endTable()
                self.startParagraph()

            elif self.line.isBlankLine:
                self.endOrgSection()
                self.endAllLists()
                self.endTable()
                self.endParagraph()
                # Do not output blank lines
                includeLine = False

            if includeLine:
                if not self.state.inBlock and not self.state.inCodeSection:
                    self.thisLine = self.applyInlineMarkup(self.thisLine)
                else:
                    self.thisLine = self.thisLine[4:]
                    self.thisLine = cgi.escape(self.thisLine)
                self.output.append(self.thisLine)

class KiwiState:
    """
    Simple class to hold the current state of the processor
    """
    inBold = False
    inItalic = False
    inParagraph = False
    inTable = False
    inList = False
    inBlock = False
    inOrgSection = False
    inCodeSection = False

class KiwiLineScanner:
    """
    Simple class to scan the current line and store details about it.
    """
    isParagraph = True
    isHeader = False
    isList = False
    isTable = False
    isTableHeader = False
    isBlock = False
    isBlank = False
    isHorizontalLine = False
    isOrgHeader = False

    headerLevel = 0
    headerText = ""

    listIndent = 0
    listText = ""

    tableColumns = []

    skipNextLine = False

    def __init__(self, mode):
        self.headerPattern = re.compile(HEADER_REGEX)
        self.listPattern   = re.compile(LIST_REGEX)
        self.tableHeaderPattern = re.compile(TABLE_HEADER_REGEX)
        self.codeStartPattern = re.compile(CODEBLOCK_START_REGEX)
        self.codeEndPattern = re.compile(CODEBLOCK_END_REGEX)
        self.mode = mode

    def reset(self):
        self.isParagraph = True
        self.isHeader = False
        self.isList = False
        self.isTable = False
        self.isTableHeader = False
        self.isBlankLine = False
        self.isBlock = False
        self.isOrgHeader = False
        self.isCodeStart = False
        self.isCodeEnd = False

        self.skipNextLine = False

        self.headerLevel = 0
        self.headerText = ""

        self.listIndent = 0
        self.listText = ""
        self.isNestedList = False

        self.codeLanguage = ""
        
        self.tableColumns = []

    def scan(self, thisLine, nextLine, state):
        """
        Main entry point. This is passed the current and next lines
        in the list, and the KiwiState instance that the main
        processor is using.
        """
        self.state = state
        self.reset()
        if thisLine.strip() == "":
            self.isBlankLine = True
            self.isParagraph = False
        else:
            self.check_for_header(thisLine, nextLine)
            self.check_for_table(thisLine, nextLine)
            self.check_for_block(thisLine)
            self.check_for_list(thisLine, nextLine)
            self.check_for_horizontal_line(thisLine)
            self.check_for_code_start(thisLine)
            self.check_for_code_end(thisLine)
            if self.mode == KIWI_MODE_ORG:
                self.check_for_org_header(thisLine)

    def check_for_header(self, thisLine, nextLine):
        # Check for '#' style of header
        match = re.search(self.headerPattern, thisLine)
        if match:
            self.isParagraph = False
            self.isHeader = True
            elements = match.groups()
            header = elements[0]
            self.headerLevel = len(header)
            if (len(elements) > 1):
                self.headerText = elements[1]
        # Check for 'underline' style of header
        elif re.search(r"^={5,}=+$", nextLine):
            self.isParagraph = False
            self.isHeader = True
            self.skipNextLine = True
            self.headerLevel = 1
            self.headerText = thisLine
        elif re.search(r"^-{5,}-+$", nextLine):
            self.isParagraph = False
            self.isHeader = True
            self.skipNextLine = True
            self.headerLevel = 2
            self.headerText = thisLine

    def check_for_list(self, thisLine, nextLine):
        match = re.search(self.listPattern, thisLine)
        if match and not self.state.inBlock:
            self.isParagraph = False
            self.isList = True

            # The regex returns the number of spaces that the
            # line is indented by, in the first match group
            self.listIndent = len(match.groups()[0])

            # The second match group holds the remainder of the
            # line following the asterisk
            self.listText  = match.groups()[1]

            # Check the next line. If it is another list entry,
            # but at a deeper indentation level, then we are
            # about to start a nested list (we need to know
            # this in advance, because HTML requires that we
            # don't close the LI tag on the current line if
            # it is followed by a sublist -- essentially the
            # sub-list in inside LI tag).
            match = re.search(self.listPattern, nextLine)
            if match:
                self.isNestedList = len(match.groups()[0]) > self.listIndent

    def check_for_table(self, thisLine, nextLine):
        """
        Checks whether the current line represents a table column. It uses
        two different criteria.

        First it checks the next line, to see if it is a table divider line.
        This is the same as standard Markdown.

        However, in the absence of a table divider it will also look for the
        presence of at least two '|' characters in the line, which will also
        be taken as indicating a table.
        """
        match = re.search(self.tableHeaderPattern, nextLine)
        if match:
            self.isTable = True
            self.isTableHeader = True
            self.skipNextLine = True

        self.tableColumns = [column.strip() for column in thisLine.split("|")]
        if (len(self.tableColumns) >= 3) or (len(self.tableColumns) > 0 and self.state.inTable):
            self.isTable = True

    def check_for_block(self, thisLine):
        """
        Checks for text which indented by at least 4 spaces, which will be
        treated as a PRE block.
        """
        if thisLine[0:4] == "    " and not self.state.inTable:
            self.isParagraph = False
            self.isBlock = True

    def check_for_horizontal_line(self, thisLine):
        """
        If we come across a row of hyphens that is not a header indicator (i.e.
        it is preceded by at least one blank line) it will be detected here and
        treated as a horizontal line
        """
        if re.search(r"^[-]{5}[-]+$", thisLine):
            self.isParagraph = False
            self.isHorizontalLine = True

    def check_for_org_header(self, thisLine):
        """
        Any line which begins (after any whitespace) with an asterisk is assumed
        to be an org-mode header. Note that this method is only called if the
        file is marked as an org-mode file.
        """
        if thisLine.strip()[0] == "*":
            self.isParagraph = False
            self.isOrgHeader = True

    def check_for_code_start(self, thisLine):
        match = re.search(self.codeStartPattern, thisLine)
        if match:
            self.isCodeStart = True
            self.codeLanguage = match.group(1)

    def check_for_code_end(self, thisLine):
        match = re.search(self.codeEndPattern, thisLine)
        if match:
            self.isCodeEnd = True
            self.codeLanguage = ""

if __name__ == "__main__":

    # For testing purposes only. Pass a file name on the command-line,
    # and it will be converted to an HTML fragment, which will then be
    # output.
    if len(sys.argv) > 1:
        f = open(sys.argv[1])
        lines = f.readlines()
        f.close()
        kiwi = KiwiMarkup()
        kiwi.execute(lines, KIWI_MODE_STD)
        print("\n".join(kiwi.output))
