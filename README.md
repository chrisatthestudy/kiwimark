# KiwiMarkup

This Python script implements the mark-up for the Kiwi system (essentially a
static website generator). It expects to be given a list of text lines
which it converts to the equivalent HTML format.

Because this is the first part of a larger system it is not really intended to
be run stand-alone, but see the "if __name___..." section at the end of the
script for simple command-line use.

## About the Mark-up

The mark-up formatting used is partially -- but only partially -- compatible
with John Gruber's 'Markdown' format.

**Historical Note**: _The original version of this was a system that would
take a folder full of text files that were roughly in Wiki format and would
convert them into web-pages. It was written many years before Markdown
appeared, but wasn't cross-platform. I switched to using Markdown when I was
searching for a cross-platform equivalent of my system, but it never quite
satisfied me, so I finally decided to do a re-write of my original version,
and this is the first part._

### Headers

Lines which are followed by a line of at least 5 '=' characters
are treated as H1.

Lines which are followed by a line of at least 5 '-' characters
are treated as H2.

Alternatively, the SETEXT format can be used, which marks headers by preceding
them with a number of '#' characters, the quantity of which indicates the
header level. Up to 6 '#' characters are allowed (there should be no spaces
between them, but there can be up to 3 whitespace characters at the very start
of the line):

    # Header 1
    ## Header 2
    ### Header 3

...etc.

Both types of header format can be mixed in the same file.

### Unordered Lists

Lines which start with a single asterisk followed by a space are treated as
list items. Any number of whitespace characters can precede the asterisk, and
the resulting indentation will allow nested lists (sublists) to be created:

    * List item 1
    * List item 2
      * Second list, item 1
      * Second list, item 2
    * List item 3

Ordered (numbered) Lists are not supported (this is deliberate -- I often
number paragraphs, and the confusion between numbered paragraphs and numbered
lists is just too awkward to handle consistently).

### URL Links

These use the Markdown style:

    [title](http://www.example.com/)

The URL format is not validated.

### Footnotes

Footnotes use the Markdown style. Use [^1] to indicate that there is a related
footnote, and then precede the footnote itself with [^1]: (the colon is
significant).

Unlike Markdown the footnotes are not renumbered, and the footnote text is not
moved to the bottom of the page (partly because I dislike both of these
features -- they are appropriate for printed formats, but not for web-pages).

### Images

There are two supported formats for image links. One is the Markdown format:

    ![alt-text](/path/to/image.png)

The other format is similar, but with the following amendments: it has no
preceding '!' character, the text inside the square brackets is required to
start with 'img', and this text can be followed by a period plus a class name
and a colon plus the alt-text. Both of the latter are optional:

    [img](/path/to/image.png)
    [img.class](/path/to/image.png)
    [img:alt-text](/path/to/image.png)
    [img.class:alt-text](/path/to/image.png)

### Bold text

Bold text should be enclosed between matching '**' characters. There is the
restriction that the start must be preceded either by whitespace or by the
start of the line, and the end must be followed either by whitespace, limited
punctuation -- one of ',', '.', ';', ')', '(', '?' or ':' -- or the end of a
line.

### Emphasized text

Emphasized text (usually italic, but this is CSS-dependent) should be enclosed
between matching '_' characters. As with bold text there is the restriction
that the start must be preceded either by whitespace or by the start of the
line, and the end must be followed either by whitespace, limited punctuation
-- one of ',', '.', ';', ')', '(', '?' or ':' -- or the end of a line.

### Tables

Table rows are indicated by lines which contain at least two '|' characters,
or by the presence of a header-divider.

The format of the header-divider can either use Markdown format or a similar
format which uses '+' instead of '|' at cell junctions:

Markdown format:

    One | Two |
    ----|-----|
    10  | ten |

Alternative format:

    One | Two |
    ----+-----+
    10  | ten |

The header line must have at least 3 hyphens to mark the first column,
otherwise the line will not be treated as a header-divider.

Headerless format:

    One | Two |
    1a  | 2a  |

### Block text

Any text which is indented by four or more white spaces will be enclosed in a
PRE tag, and will be ignored by all the other processing -- the text will be
output exactly as-is. The only change will be to escape any HTML tags, to
prevent these being treated as actual HTML.

### org-mode

Although org-mode is not really handled, the mark-up processor will recognise
org-mode files, provided they include the standard org-mode indicator,
-*- mode: org -*-, on the first line.

If this is detected, org-mode headers which are on consecutive lines will be
kept separate rather than being merged together into a single paragraph, and
the detection of bold sections will be suppressed for these lines (as the
asterisks that indicate org-mode headers would otherwise result in
false-positives).


