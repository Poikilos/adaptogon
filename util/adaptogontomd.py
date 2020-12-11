#!/usr/bin/env python
"""
Fix csv files created from mysql tables which have newlines in the
fields. To avoid broken CSV files, you must specify a custom newline and
re-export as follows before running this code.

1. do something like: `sudo su -`, then  `mysql`, then `USE`
followed by then name of the database you want to export.

2.

SELECT * INTO OUTFILE 'streetlightinfo-last-php-version.csv'
  FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
  LINES TERMINATED BY 'SUPER_SAYAN_NEWLINE_HERE'
  FROM sections;
3.
quit;

This program will only do as much about blank lines as it can without
mangling the HTML (shoving words together). If there is HTML like
`line. <br /> <br />Another line` you can expect the markdown to have
3 blank lines in between the two, the middle having only a space,
because that's what the HTML said to do.
"""
import os
csvNL = "SUPER_SAYAN_NEWLINE_HERE" # must be the same used in mysql dump
literalNL = "__LITERAL_NEWLINE__"
dirPath = "/home/owner/www/streetlightinfo-last-php-version/backup-php-deprecated"
path = os.path.join(dirPath, "streetlightinfo-last-php-version.csv")
dest = os.path.join(dirPath, "streetlightinfo-last-php-version-fixed.csv")
dat = ""
with open(path, 'r') as ins:
    for misalignedLine in ins:
        line = misalignedLine.strip()
        if len(line) < 1:
            continue
        dat += line + literalNL

lines = dat.split(csvNL)
with open(dest, 'w') as outs:
    for i in range(len(lines)):
        realLine = lines[i]
        # fix mysql command's shortcomings:
        line = realLine.replace("\\N", "")
        # ^ null is `` not `\N` in csv
        line = line.replace("\\S", "S")
        line = line.replace("\\\"", "\"\"")
        # ^ double quote is `""` not `\"` in csv
        line = realLine.replace("\\'", "")
        # ^ from magic slashes
        while (literalNL+literalNL) in line:
            line = line.replace(literalNL+literalNL, literalNL)
        if line.strip() == literalNL:
            continue
        if len(line.strip()) < 1:
            continue
        outs.write(line+'\n')
# optional (adaptogon-specific code):
# titles = None
# row names:
"""
sudo su -
mysql
use str33t1xght;
SHOW COLUMNS FROM sections;
quit;
"""
# ^ Table names are case sensitive.
# numbers added:
"""
+-----------------+------------------+------+-----+---------------------+-------------------------------+
|  Field           | Type             | Null | Key | Default             | Extra                         |
+-----------------+------------------+------+-----+---------------------+-------------------------------+
| 0 SectionID       | int(10) unsigned | NO   | PRI | NULL                | auto_increment                |
| 1 Parent          | int(10) unsigned | NO   |     | 0                   |                               |
| 2 Title           | tinytext         | NO   |     | NULL                |                               |
| 3 Subtitle        | tinytext         | YES  |     | NULL                |                               |
| 4 DateTimeUpdated | timestamp        | NO   |     | current_timestamp() | on update current_timestamp() |
| 5 LeftText        | mediumtext       | YES  |     | NULL                |                               |
| 6 MainText        | mediumtext       | YES  |     | NULL                |                               |
| 7 RightText       | mediumtext       | YES  |     | NULL                |                               |
| 8 FakeSelfHref    | varchar(128)     | NO   |     |                     |                               |
| 9 Tags            | mediumtext       | NO   |     | NULL                |                               |
|10 Attrib          | varchar(32)      | YES  |     | NULL                |                               |
+-----------------+------------------+------+-----+---------------------+-------------------------------+
"""
from csv import reader
idI = 0
parentI = 1
shortNameI = 2
headingAndTaglineI = 3
LeftTextI = 5
RightTextI = 7
updatedI = 4
bodyI = 6
htmlRefI = 8
TagsI = 9
AttribI = 10
parentNames = {}
treePath = os.path.join(dirPath, 'tree-md')
if not os.path.isdir(treePath):
    os.makedirs(treePath)

from html.parser import HTMLParser

with open(dest, 'r') as read_obj:
    # pass the file object to reader() to get the reader object
    csv_reader = reader(read_obj)
    # Iterate over each row in the csv using reader object
    for row in csv_reader:
        # Use the int in text form as the index for easy write/lookup.
        # parentNames[str(htmlRefI)] = row[htmlRefI]
        permaLinkNoExt = os.path.splitext(row[htmlRefI])[0]
        parentNames[str(row[idI])] = permaLinkNoExt

print("* detected names for later use as parent"
      " (in case another page uses it as a parent): {}"
      "".format(parentNames))


def debad(htmlS):
    """
    Only run this on HTML! Two newlines in _markdownAndFlags ends a paragraph,
    and may be intentional.
    """
    badNL = ["\n\n", "\n ", " \n"]
    for bad in badNL:
        while bad in htmlS:
            htmlS = htmlS.replace(bad, "\n")
    return htmlS


def getAnyEnd(haystack, needles, orSpace=False):
    ret = None
    for needle in needles:
        if haystack.endswith(needle):
            return needle
    if orSpace:
        if haystack[-1:] != haystack[-1:].strip():
            return haystack[-1:]
    return None


def getAnyStart(haystack, needles, orSpace=False):
    ret = None
    for needle in needles:
        if haystack.startswith(needle):
            return needle
    if orSpace:
        if haystack[:1] != haystack[:1].strip():
            return haystack[:1]
    return None


def stripMore(htmlS):
    moreSpaces = ["&nbsp;", "\\n", "\\r", "\\t", "\\N"]
    # ^ mutilated by CMS, mysql, or magic quotes
    #   `\N`: mysql escape sequence for NULL
    htmlS = htmlS.strip()
    while True:
        got = getAnyEnd(htmlS, moreSpaces, orSpace=True)
        if got is None:
            break
        htmlS = htmlS[:-len(got)]

    while True:
        got = getAnyStart(htmlS, moreSpaces, orSpace=True)
        if got is None:
            break
        htmlS = htmlS[len(got):]

    htmlS = htmlS.strip()

    return htmlS




class Tag:
    """
    Tag represents an HTML opening tag including its attributes.
    Tag is the class that contains attributes, and tagWord is the
    .
    """
    def __init__(self, tagWord, attrs):
        """
        Sequential arguments:
        tagWord -- the so-called "tag" provided by HTMLParser, which is
                   actually a string (tagword, to avoid ambiguity).
        attrs -- a list of (key, value) tuples as provided by HTMLParser
        """
        self.tagWord = tagWord
        self.attrs = attrs
        "so-called html 'tag' which is really just one word"

    def __str__(self):
        return self.tw()

    def __repr__(self):
        return self.tw()

    def styles(self):
        """
        Get a list of (name, value) style tuples (lowercase).
        """
        style = None
        styles = None
        for attrib, v in self.attrs:
            if attrib.lower() == "style":
                style = v
        if style is not None:
            assignments = style.split(";")
            for s in assignments:
                if s.strip() == "":
                    continue
                k, v = s.split(":")
                k = k.strip()
                v = v.strip()
                # print("style property {}:{}".format(k, v))
                if styles is None:
                    styles = []
                styles.append((k, v))
                # print("style property {}".format(styles[-1]))
        return styles

    def get(self, attribName):
        """
        Get a plain html attribute.
        """
        name = attribName.lower()
        for attrib, v in self.attrs:
            if attrib.lower() == name:
                return v
        return None

    def hasStyle(self, name, value):
        """
        Sequential arguments:
        name -- a style property name (case-insensitive)
        value -- a style property value (case-insensitive) or "*"
                 for any (as long as name matches)
        """
        styles = self.styles()
        if styles is None:
            return False
        for style in styles:
            k, v = style
            if k.lower() == name.lower():
                if value == "*":
                    return True
                if v.lower() == value.lower():
                    return True
        return False

    def tw(self):
        """
        Get a lowercase version of the tagword.
        """
        return self.tagWord.lower()


class MDFromHTMLParser(HTMLParser):

    COMPLEX_NEWLINES = ['p', 'div', 'ul', 'ol']
    MD_NEWLINE = "\\"
    OPTIONAL_VOIDS = ["li"]
    H_LEVELS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    FLAG_TAGS = [
        "table",
        "tr",
        "th",
        "thead",
        "tbody",
        "td",
    ]

    FLAG_TAG_LT = "__ADAPTOGON_GT__"
    FLAG_TAG_GT = "__ADAPTOGON_LT__"
    FLAG_TAG_LB = "__ADAPTOGON_LB__"
    FLAG_TAG_RB = "__ADAPTOGON_RB__"
    FLAG_TAG_ST = "__ADAPTOGON_ST__"

    FLAG_TAG_SBQ = "__ADAPTOGON_START_BLOCK_QUOTE_LINE__"
    # ^ convert to flags

    _KEEP_HTML = {
        "sup": ["__ADAPTOGON_CARET__", "^"],
        "sub": ["__ADAPTOGON_TILDE__", "~"],
    }


    def __init__(self, enableSubSup=True, enableVuePress=True, tb=None):
        """

        Keyword arguments:
        enableSubSup -- Change <sup> and </sup> to ^, change <sub> and
                        </sub> to ~ in accordance with markdown sub-sub
                        for VuePress. Set enableSubSup to False if you
                        don't have an addon which changes ^2^ to
                        squared and B~1~ to B sub 1.
                        <https://vuepress-theme.mrhope.site/guide/
                        feature/markdown/sup-sub/#configuration>
        enableVuePress -- Change URLs without slashes that end in
                          `.html` to `.md`. Set enableVuePress to false
                          if you don't want that.
        tb -- a file that produced the HTML, for tracing
        """
        super().__init__()
        self.wasB = False
        self.wasI = False
        self.wasST = False
        self.tb = tb
        self.enableSubSup = enableSubSup
        self.enableVuePress = enableVuePress
        self._markdownAndFlags = ""
        self.path = None
        self.voids = [
            'area', 'base', 'br', 'col', 'command', 'embed', 'hr',
            'img', 'input', 'keygen', 'link', 'meta', 'param',
            'source', 'tb', 'wbr'
        ]
        # ^ See
        # https://www.w3.org/TR/2011/WD-html-markup-20110405/syntax.html
        self.debugPrevData = None
        self.debugPrevPrevData = None
        self.stack = []
        self.boldAt = -1
        self.iAt = -1
        self.stAt = -1
        self.bTags = ['bold', 'b', 'strong']
        self.iTags = ['i', 'italic']
        self.stTags = ['strike']
        self.olLiN = 1
        self.lastUrl = None
        self.liSpaces = []
        self.poppedSpaces = True

        self.boldStyles = [
            ("font-weight", "bold"),
            ("font-weight", "bolder"),
            ("font-weight", "500"),
            ("font-weight", "600"),
            ("font-weight", "700"),
            ("font-weight", "800"),
            ("font-weight", "900"),
            # ^ See https://www.w3schools.com/cssref/pr_font_weight.asp
            #   Can be a number (not only bold or bolder)
            #   ...where 400 is normal!
            #   - Other less than bold weights: normal, lighter
            #   - Other values to ignore (For _markdownAndFlags, who
            #     cares--leave it normal): inherit, initial
        ]
        self.emStyles = [
            ("font-style", "italic"),
            ("font-style", "oblique"),
        ]
        self.stStyles = [
            ("text-decoration", "line-through"),
        ]

    @staticmethod
    def _insulate(self, tagWord):
        LT = MDFromHTMLParser.FLAG_TAG_LT
        GT = MDFromHTMLParser.FLAG_TAG_GT
        return LT + tagWord + GT


    def keep(self):
        keep = {}
        lose = []
        if not self.enableSubSup:
            lose = ["sub", "sub"]
        for k, v in MDFromHTMLParser._KEEP_HTML.items():
            if k not in lose:
                keep[k] = v
        return keep


    def keepFlag(self, k):
        return self.keep()[k][0]


    def keepHTML(self, k):
        return self.keep()[k][1]


    def getMarkdown(self):
        """
        Get markdown and tables and sup and sub
        """
        LT = MDFromHTMLParser.FLAG_TAG_LT
        GT = MDFromHTMLParser.FLAG_TAG_GT
        LB = MDFromHTMLParser.FLAG_TAG_LB
        RB = MDFromHTMLParser.FLAG_TAG_RB
        SBQ = MDFromHTMLParser.FLAG_TAG_SBQ
        md = self._markdownAndFlags
        """
        # Make all LT and GT into literals before adding actual html:
        lines = md.split("\n")
        md = ""
        for line in lines:
            if not line.startswith("> "):
                line = line.replace("<", "\\<")
                line = line.replace(">", "\\>")
            else:
                line = (
                    "> "
                    + line[2:].replace("<", "\\<").replace(">", "\\>")
                )
            md += line + "\n"
        # handle via SBQ instead:
        """
        replacements = {
            "<": "\\<",
            ">": "\\>",
            "[": "\\[",
            "]": "\\]",
        }
        replacements[SBQ + "\n" + SBQ] = ""
        for old, new in replacements.items():
            md = md.replace(old, new)

        md = md.replace(SBQ, "> ")
        md = md.replace(GT, ">")
        md = md.replace(LT, "<")
        md = md.replace(LB, "[")
        md = md.replace(RB, "]")
        # Re-add HTML parts AFTER making all LT and GT into literals:

        for tagWord, vals in self.keep().items():
            old, new = vals
            md = md.replace(old, new)



        redundantExplicitMDNLs = [
            "\\\n\n",
            "\n\n\\",
            "\\\n\\\n",
            "\\\\",
            "\\\n \\",
            "\\\n  \\",
            "\n \\\n",
            "\n\\\n",
        ]

        # This is hacky but may work (repeat since only the collapsed
        # version will match in some cases, it seems):
        for badNL in redundantExplicitMDNLs:
            while badNL in md:
                for badNL2 in redundantExplicitMDNLs:
                    while badNL2 in md:
                        md = md.replace(badNL2, "\n\n")
        for badNL in redundantExplicitMDNLs:
            while badNL in md:
                for badNL2 in redundantExplicitMDNLs:
                    while badNL2 in md:
                        md = md.replace(badNL2, "\n\n")

        old = "\n\n\n"
        new = "\n\n"
        while old in md:
            md = md.replace(old, new)
        replacements = {
            "\\\n# ": "\n\n# ",
            "\\\n## ": "\n\n## ",
            "\\\n### ": "\n\n### ",
            "\\\n#### ": "\n\n#### ",
            "\\\n##### ": "\n\n##### ",
            "\\\n###### ": "\n\n###### ",
        }
        for old, new in replacements.items():
            md = md.replace(old, new)

        return md


    def push(self, tagWord, attrs):
        """
        Push if not a void tag (if not a self-closing tag).
        """
        if tagWord.lower() not in self.voids:
            self.stack.append(Tag(tagWord, attrs))


    def isIn(self, tagWord, orStyles=None, depth=None):
        """
        Find out whether something is in the tag stack (self.stack).
        Sequential arguments:
        tagWord -- a string or list of strings to find in the tag stack

        Keyword arguments:
        orStyle -- an array of style tuples, such as:
                   [("font-style","italic"), ("font-style","oblique")]
        depth -- the count of stack items to check (1 for top tag only)
        """
        tagWords = [tagWord]

        if hasattr(tagWord, 'append'):
            tagWords = tagWord
        stack = self.stack
        if depth is not None:
            stack = self.stack[-depth:]
        for tag in stack:
            thisTagWord = str(tag)
            for tagWord in tagWords:
                tagWord = tagWord.lower()
                if tagWord == thisTagWord:
                    return True
            if orStyles is not None:
                for orStyle in orStyles:
                    try:
                        k, v = orStyle
                        if tag.hasStyle(k, v):
                            return True
                    except ValueError as ex:
                        print("orStyle: {}".format(orStyle))
                        raise ex
        return False


    def pop(self, tagWord):
        if len(self.stack) < 1:
            print("ERROR: there are no open tags before </{}> in {}"
                  " near \"{}\" after \"{}\" in file {}"
                  "".format(tagWord, self.stack, self.debugPrevData,
                            self.debugPrevPrevData, self.path))
            return None
        ret = self.stack[-1]
        tw = tagWord.lower()
        if ret.tw() != tw:
            if ret.tw() in MDFromHTMLParser.OPTIONAL_VOIDS:
                if len(self.stack) >= 2:
                    del self.stack[-1]
                    ret = self.stack[-1]
        if ret.tw() != tw:
            raise SyntaxError("ERROR: <{}> doesn't preceed </{}> in {}"
                              " in file {} near \"{}\" after \"{}\""
                              ". Maybe one of the enclosing tags"
                              " needs to be removed or closed first."
                              "".format(tagWord, tagWord,
                                        self.stack, self.path,
                                        self.debugPrevData,
                                        self.debugPrevPrevData))
        del self.stack[-1]
        return ret

    def handle_starttag(self, tagWord, attrs):
        tw = tagWord.lower()
        LB = MDFromHTMLParser.FLAG_TAG_LB
        ST = MDFromHTMLParser.FLAG_TAG_ST
        LB = MDFromHTMLParser.FLAG_TAG_LB
        RB = MDFromHTMLParser.FLAG_TAG_RB
        if tw == "ol":
            self.olLiN = 1

        if tw in MDFromHTMLParser.COMPLEX_NEWLINES:
            self._markdownAndFlags += "\n\n"

        topWord = None
        if len(self.stack) > 0:
            topWord = self.stack[-1]
        if tw == "li":
            if not self.poppedSpaces:
                del self.liSpaces[-1]
            if topWord == "ol":
                new = "\n{}. ".format(self.olLiN)
            else:
                new = "\n- "
            self._markdownAndFlags += new
            newSpaces = " " * (len(new)-1)  # -1 for newline
            self.liSpaces.append(newSpaces)
            self.poppedSpaces = False
        newTag = Tag(tagWord, attrs)
        self.push(tagWord, attrs)  # only pushes not a void tag
        if (tw == "code") and not self.isIn("pre"):
            self._markdownAndFlags += "\n```\n"
        elif (tw == "pre") and not self.isIn("code"):
            self._markdownAndFlags += "\n```\n"
        elif tw == "img":
            alt = newTag.get("alt")
            src = newTag.get("src")
            if src is None:
                print("WARNING: img has no src in file {}".format(tb))
            else:
                if alt is None:
                    alt = src
                self._markdownAndFlags += "!{}{}{}({})".format(
                    LB,
                    alt,
                    RB,
                    src,
                )
        elif tw == "a":
            self.lastUrl = newTag.get("href")
            if self.lastUrl is not None:
                self._markdownAndFlags += LB

        got = self.keep().get(tw)
        if got is not None:
            FLAG, REAL = got
            self._markdownAndFlags += FLAG

        """
        if self.isIn(self.bTags, orStyles=self.boldStyles, depth=1):
            self._markdownAndFlags += '**'
            self.bAt = len(self.stack)
        elif self.isIn(self.iTags, orStyles=self.emStyles, depth=1):
            self._markdownAndFlags += '_'
            self.iAt = len(self.stack)
        elif self.isIn(self.stTags, orStyles=self.stStyles, depth=1):
            self._markdownAndFlags += ST
            self.stAt = len(self.stack)
        """
        if tw == "br":
            self._markdownAndFlags += MDFromHTMLParser.MD_NEWLINE + "\n"
        LT = MDFromHTMLParser.FLAG_TAG_LT
        GT = MDFromHTMLParser.FLAG_TAG_GT

        if tw in MDFromHTMLParser.FLAG_TAGS:
            self._markdownAndFlags += LT + "{}".format(tw) + GT


    def handle_endtag(self, tagWord):
        tw = tagWord.lower()
        LT = MDFromHTMLParser.FLAG_TAG_LT
        GT = MDFromHTMLParser.FLAG_TAG_GT
        LB = MDFromHTMLParser.FLAG_TAG_RB
        RB = MDFromHTMLParser.FLAG_TAG_RB
        ST = MDFromHTMLParser.FLAG_TAG_ST

        got = self.keep().get(tw)
        if got is not None:
            FLAG, REAL = got
            self._markdownAndFlags += FLAG

        if tw in MDFromHTMLParser.FLAG_TAGS:
            self._markdownAndFlags += LT + "/{}".format(tw) + GT
        elif tw == "li":
            if len(self.liSpaces) < 1:
                raise ValueError("</li> before <li> in {}"
                                 "".format(self.path))
            else:
                del self.liSpaces[-1]
            self.poppedSpaces = True
        if tw == "br":
            # ^ Why does this happen in handle_endtag??
            self._markdownAndFlags += MDFromHTMLParser.MD_NEWLINE + "\n"
        else:
            self.pop(tw)
        # Handle </code></pre> vs </pre></code> AFTER pop, to reverse
        # the handle_starttag condition (get all the way out of the
        # 2-deep block).

        if (tw == "code") and not self.isIn("pre"):
            self._markdownAndFlags += "\n```\n"
        elif (tw == "pre") and not self.isIn("code"):
            self._markdownAndFlags += "\n```\n"
        elif tw == "a":
            if self.lastUrl != None:
                self._markdownAndFlags += RB
                url = self.lastUrl
                if not "/" in url:
                    # adaptogon-specific--index.php serves all files
                    # so anything without slashes is internal.
                    if self.enableVuePress:
                        badExt = ".html"
                        if url.endswith(badExt):
                            url = url[:-len(badExt)] + ".md"
                self._markdownAndFlags += "({})".format(url)

        """
        if self.isIn(self.bTags, orStyles=self.boldStyles, depth=1):
            self._markdownAndFlags += '**'
            self.bAt = len(self.stack)
        elif self.isIn(self.iTags, orStyles=self.emStyles, depth=1):
            self._markdownAndFlags += '_'
            self.iAt = len(self.stack)
            print("END OF {} after {}".format("italics (any)", self.debugPrevData))
        elif self.isIn(self.bTags, orStyles=self.stStyles, depth=1):
            self._markdownAndFlags += ST
            self.bAt = len(self.stack)
        """
        if tw in MDFromHTMLParser.H_LEVELS:
            # print("END OF {} after {}".format(tw, self.debugPrevData))
            self._markdownAndFlags += "\n"


    def handle_data(self, data):
        # Mimic html behavior where each whitespace area is one space:
        data = data.replace ("\n", " ")
        data = data.replace ("\r", " ")
        data = data.replace ("\t", " ")
        while "  " in data:
            data = data.replace("  ", " ")
        if data == data.strip():
            data = data.strip()
            # ^ allow later cleanup to detect multiple newlines
        indent = "".join(self.liSpaces)
        ST = MDFromHTMLParser.FLAG_TAG_ST
        SBQ = MDFromHTMLParser.FLAG_TAG_SBQ
        # if self.isIn("li"):
        # #   data = indent + data.replace("\n", "\n" + indent)
        # TODO:? ^
        top = None
        if len(self.stack) > 0:
            top = self.stack[-1]

        top = None
        if len(self.stack) > 0:
            top = self.stack[-1].tw()
        before = ""
        after = ""

        data = data.replace("*", "\\*")
        data = data.replace("_", "\\_")

        if self.isIn(self.bTags, orStyles=self.boldStyles, depth=1):
            before += '**'
            after = '**' + after
            if self.wasB or self.wasI or self.wasST:
                before = " " + before
                # ^ try to prevent broken markdown from multiple marks
            # self._markdownAndFlags += '**'
            # self.bAt = len(self.stack)
            self.wasB = True
            self.wasI = False
            self.wasST = False
        elif self.isIn(self.iTags, orStyles=self.emStyles, depth=1):
            before += '_'
            after = '_' + after
            # self._markdownAndFlags += '_'
            # self.iAt = len(self.stack)
            self.wasB = False
            self.wasI = True
            self.wasST = False
        elif self.isIn(self.stTags, orStyles=self.stStyles, depth=1):
            before += ST
            after = ST + after
            # self._markdownAndFlags += ST
            # self.stAt = len(self.stack)
            self.wasB = False
            self.wasI = False
            self.wasST = True

        if top is not None:
            if top in MDFromHTMLParser.H_LEVELS:
                i = MDFromHTMLParser.H_LEVELS.index(top)
                before = "\n\n" + "#"*i + " "
                # ^ newline after the line is handled by endtag handler

        if self.isIn("blockquote"):
            if top == "blockquote":
                data = SBQ + data
            data = data.replace("\n", "\n" + SBQ)

        # if self.isIn(bTags, orStyles=self.boldStyles):
        # #   data = '**{}**'.format(data)
        # if self.isIn(iTags, orStyles=self.emStyles):
        # #   data = '_{}_'.format(data)
        # if self.isIn(stTags, orStyles=self.stStyles):
        # #   data = '_{}_'.format(data)
        # data = MDFromHTMLParser.stripLineByLine(data)
        # ^ stripLineByLine BREAKS ABOVE WORK, don't do it.
        if len(data) > 0:
            self.debugPrevPrevData = self.debugPrevData
            self.debugPrevData = data
            self._markdownAndFlags += before + data + after


    @staticmethod
    def stripLineByLine(htmlS):
        badNLs = [" \n", "\n "]
        new = "\n"
        for old in badNLs:
            while old in htmlS:
                htmlS = htmlS.replace(old, new)
        return htmlS


def toMarkdown(htmlS, tb=None):
    """
    Keyword arguments:
    tb -- The file that originated the content, for error-tracing
    """
    parser = MDFromHTMLParser(tb=tb)
    parser.path = tb
    parser.feed(htmlS)
    # ^ feed is synchronous
    # print("parser._markdownAndFlags: {}".format(parser._markdownAndFlags))
    if len(parser.stack) > 0:
        raise ValueError(
            "For HTML tag(s) not closed ({}) you must remove"
            " the tag (fails if in Subtitle): {}\n near \"{}\" in: {}"
            "".format(parser.stack, tb, parser.debugPrevData,
                      parser.stack)
        )
    htmlS = parser.getMarkdown()
    return htmlS
    """
    # DEPRECATED:
    void = "link"  # random void (self-terminating) tag
    htmlS = htmlS.replace("_", "\\_")
    htmlS = htmlS.replace("*", "\\*")
    htmlS = htmlS.replace(' style="font-family: Arial;"', ' ')
    htmlS = htmlS.replace(' style="font-family: Arial"', ' ')
    # Wait to do entities until the end, to avoid seeing them
    # as syntax!
    bads = ['small', 'big']

    # BAD
    casedBads = bads + [bad.upper() for bad in bads]
    # print("casedBads: {}".format(casedBads))
    for s in casedBads:
        htmlS = htmlS.replace("<{}>".format(s), "")
        htmlS = htmlS.replace("</{}>".format(s), "")
        # destroy any styled ones:
        htmlS = htmlS.replace("<{} ".format(s), "<{} ".format(void))

    # BOLD
    bolds = ['b', 'bold', 'strong']
    casedBolds = bolds + [bold.upper() for bold in bolds]
    # print("casedBolds: {}".format(casedBolds))
    for s in casedBolds:
        htmlS = htmlS.replace("<{}>".format(s), "**")
        htmlS = htmlS.replace("</{}>".format(s), "**")
        # destroy any styled ones:
        htmlS = htmlS.replace("<{} ".format(s), "**<{} ".format(void))

    # ITALICS
    emphatics = ['i', 'italics', 'em']
    casedEmphatics = emphatics + [em.upper() for em in emphatics]
    # print("casedEmphatics: {}".format(casedEmphatics))
    for s in casedEmphatics:
        htmlS = htmlS.replace("<{}>".format(s), "_")
        htmlS = htmlS.replace("</{}>".format(s), "_")
        # destroy any styled ones:
        htmlS = htmlS.replace("<{} ".format(s), "_<{} ".format(void))


    lis = ["li"]
    casedLis = lis + [s.upper() for s in lis]
    for s in casedLis:
        htmlS = htmlS.replace("<{}>".format(s), "\n- ")
        htmlS = htmlS.replace("</{}>".format(s), "\n")
        # destroy any styled ones:
        htmlS = htmlS.replace("<{} ".format(s), "\n- <{} ".format(void))

    htmlS = stripMore(htmlS)

    COMPLEX_NEWLINES = MDFromHTMLParser.COMPLEX_NEWLINES
    new = "\n"
    complex1 = [COMPLEX_NEWLINES, new]

    complexSpans = ['span']
    new = ''
    complex2 = [complexSpans, new]

    complexes = [complex1, complex2]

    modifiers = {}
    modifiers['align'] = ['left', 'center', 'right']
    modifiers['style'] = [
        'text-align: center',
        'padding-left: 30px',
        'text-align: left',
        'text-align: right',
        'margin-left: 40px',
    ]
    more = [(s + ";") for s in modifiers['style']]
    modifiers['style'] = modifiers['style'] + more

    for cx in complexes:
        COMPLEX_NEWLINES, new = cx

        cased = COMPLEX_NEWLINES + [s.upper() for s in COMPLEX_NEWLINES]

        for bareS in cased:
            htmlS = htmlS.replace("<{}>".format(bareS), "\n")
            htmlS = htmlS.replace("</{}>".format(bareS), "\n")
            # ^ </p><p> should become \n\n, since that is a paragraph
            #   break in _markdownAndFlags. Only br* should become
            #   MDFromHTMLParser.MD_NEWLINE
            for attrib, values in modifiers.items():
                for value in values:
                    s = '{}="{}"'.format(attrib, value)
                    old = "<{} {}>".format(bareS, s)
                    htmlS = htmlS.replace(old, new)
                    # Handle multiple modifiers in any order:
                    for attrib2, values2 in modifiers.items():
                        for value2 in values2:
                            s2 = '{}="{}"'.format(attrib2, value2)
                            old = "<{} {} {}>".format(bareS, s, s2)
                            htmlS = htmlS.replace(old, new)
                            old = "<{} {} {}>".format(bareS, s2, s)
                            htmlS = htmlS.replace(old, new)
                    # destroy any with unknown styles:
                    htmlS = htmlS.replace("<{} ".format(s), "<{} ".format(void))
                    # print("Replacing {} with {}".format("<{} ".format(s),
                    # #                                   "<{} ".format(void)))

    horribles = [
        '_<span> </span>_',
        '<span> </span>',
        '**<span> </span>**',
        '_<span></span>_',
        '<span></span>',
        '**<span></span>**',
    ]
    for horrible in horribles:
        htmlS = htmlS.replace(horrible, "")


    casedBQs = ["<blockquote> ", "<blockquote>\n"]
    casedBQs = casedBQs + [bad.upper() for bad in casedBQs]
    anyFound = True
    while anyFound:
        # Keep looping in case " \n" becomes "\n" or something like that
        # happens.
        anyFound = False
        for casedBQ in casedBQs:
            while casedBQ in htmlS:
                anyFound = True
                htmlS = htmlS.replace(casedBQ, casedBQ[:-1])
    casedBQs = ["<blockquote>"]
    casedBQs = casedBQs + [bad.upper() for bad in casedBQs]
    for casedBQ in casedBQs:
        htmlS = htmlS.replace(casedBQ, "\n" + casedBQ)
    for nlCasedBQ in ["\n\n" + casedBQ for casedBQ in casedBQs]:
        htmlS = htmlS.replace("\n\n" + casedBQ, "\n" + casedBQ)
    for casedBQ in casedBQs:
        htmlS = htmlS.replace(casedBQ, "> ")
        # ^ _markdownAndFlags blockquote

    htmlS = stripMore(htmlS)
    htmlS = MDFromHTMLParser.stripLineByLine(htmlS)
    tooManyNL ="\n\n\n"
    justEnoughNL = "\n\n"
    # ^ Keeping double newlines is the strategy here, to account for
    #   paragraph breaks etc (</p><p> should become \n\n)
    while tooManyNL in htmlS:
        htmlS = htmlS.replace(tooManyNL, justEnoughNL)

    htmlS = htmlS.replace("&amp;", "&")
    htmlS = htmlS.replace("&nbsp;", " ")
    brs = ["<br>","<br/>", "<br />"]
    MDNL = MDFromHTMLParser.MD_NEWLINE
    casedBrs = brs + [s.upper() for s in brs]
    for s in casedBrs:
        htmlS = htmlS.replace(s, MDNL + "\n")
    while MDNL + "\n\n" in htmlS:
        htmlS = htmlS.replace(MDNL + "\n\n", MDNL + "\n")

    htmlS = htmlS.replace(" >", ">")
    htmlS = htmlS.replace("&nbsp;", " ")
    replacements = {
        '&ldquo;': '"',
        '&rdquo;': '"',
        '&lsquo;': "'",
        '&rsquo;': "'",
        '&nbsp;': " ",
        # '&#8203;': "",  # 0-width space
        # "&ZeroWidthSpace;": ""
        # "&zerowidthspace;": ""
    }
    # ^ Keep &ZeroWidthSpace; since it is good for justified text
    #   (scripted hyphenation).
    for old, new in replacements.items():
        htmlS = htmlS.replace(old, new)
    old = " >"
    new = ">"
    while old in htmlS:
        htmlS = htmlS.replace(old, new)

    bads = [
        '<sup',
        '<sub',
        'font-style: italic',
        'font-style:italic',
        'font-weight:normal',
        'font-weight: normal',
        'font-weight: bold',
        'font-weight:bold',
    ]

    casedBads = bads + [bad.upper() for bad in bads]
    for bad in casedBads:
        if bad in htmlS:
            print("  - WARNING: contains {}".format(bad))
    return htmlS
    """


def lessHTML(htmlS, removeMore=[]):
    """
    Keyword arguments:
    removeMore -- a list of tags (lowercase) to remove in addition to
                  the default ones.
    """
    if not hasattr(removeMore, 'append'):
        raise ValueError("removeMore can only be a list.")
    gones = ['p', 'br', 'div', 'small', 'big'] + removeMore
    oneGones = ['br']
    for gone in gones:
        htmlS = htmlS.replace("<{}>".format(gone), "")
        htmlS = htmlS.replace("<{}>".format(gone.upper()), "")
        htmlS = htmlS.replace("</{}>".format(gone), "")
        htmlS = htmlS.replace("</{}>".format(gone.upper()), "")
    for gone in oneGones:
        htmlS = htmlS.replace("<{}/>".format(gone), "")
        htmlS = htmlS.replace("<{}/>".format(gone.upper()), "")
    return htmlS


def splitHtmlSubtitle(heading, tagline):
    """
    If the tagline contains a BR tag (is two lines in html),
    change heading to line 1 and slice tagline
    so it becomes line 2. Discard the BR.

    returns:
    A tuple of the new (heading, tagline)
    """
    brI = -1
    brs = ["<br>", "<br/>", "<BR>", "<BR/>"]
    for br in brs:
        brI = tagline.find(br)
        if brI >= 0:
            heading = tagline[:brI]
            tagline = tagline[brI+len(br):]
            break
    return heading, tagline

def splitMDSubtitle(heading, tagline):
    """
    If the tagline contains a BR tag (is two lines in html),
    change heading to line 1 and slice tagline
    so it becomes line 2. Discard the BR.

    returns:
    A tuple of the new (heading, tagline)
    """
    brI = -1
    brs = [MDFromHTMLParser.MD_NEWLINE]
    for br in brs:
        brI = tagline.find(br)
        if brI >= 0:
            heading = tagline[:brI]
            tagline = tagline[brI+len(br):]
            break
    return heading, tagline

with open(dest, 'r') as read_obj:
    # pass the file object to reader() to get the reader object
    csv_reader = reader(read_obj)
    # Iterate over each row in the csv using reader object
    for row in csv_reader:
        for i in range(len(row)):
            row[i] = row[i].replace(literalNL, "\n")
        # print("* creating md for {}".format(row[htmlRefI]))
        permaLinkNoExt = os.path.splitext(row[htmlRefI])[0]
        sub = permaLinkNoExt + ".md"
        subSub = sub
        subSubPath = os.path.join(treePath, sub)
        if row[idI] == "0":
            subSubPath = os.path.join(treePath, "index.md")
        elif row[parentI] != "0":
            parentName = parentNames[str(row[parentI])]
            parentPath = os.path.join(treePath, parentName)
            if not os.path.isdir(parentPath):
                os.makedirs(parentPath)
            subSubPath = os.path.join(treePath, parentName, sub)
        # print("* parent is {}".format(row[parentI]))
        print("* creating {}".format(subSubPath))
        with open(subSubPath, 'w') as outs:
            outs.write("---\n")
            outs.write("created: ~{}\n".format(row[updatedI]))
            # ^ actually this is unknown, so prepend ~
            outs.write("updated: {}\n".format(row[updatedI]))
            tags = row[TagsI].strip()
            if len(tags) > 0:
                outs.write("tags: {}\n".format(tags))
            attrib = row[AttribI].strip()
            if len(attrib) > 0:
                outs.write("attrib: {}\n".format(attrib))
            outs.write("---\n")

            heading = toMarkdown(row[shortNameI])
            tagline = toMarkdown(row[headingAndTaglineI])
            heading = heading.replace("**", "")
            tagline = tagline.replace("**", "")

            heading, tagline = splitMDSubtitle(
                heading,
                tagline
            )
            tagline = tagline.strip()
            heading = heading.strip()
            outs.write("# " + heading + "\n")
            if (len(tagline) > 0) and (tagline.lower() != heading.lower()):
                tagline = tagline.replace("**", "")
                tagline = tagline.replace("_", "")
                tagline = "_{}_".format(tagline)
                # print("* Tagline \"{}\" is not heading \"{}\""
                # #     ".".format(tagline, heading))
                outs.write(tagline + "\n\n")

            """
            # Splitting this way breaks the html, such as if a tag
            # starts in one part and ends in the next.
            heading, tagline = splitHtmlSubtitle(
                row[shortNameI],
                row[headingAndTaglineI]
            )
            heading = toMarkdown(lessHTML(heading), tb=subSubPath)
            tagline = toMarkdown(lessHTML(tagline), tb=subSubPath)
            heading = lessHTML(heading)
            tagline = lessHTML(tagline)
            outs.write("# " + heading + "\n")
            if heading != tagline:
                outs.write(tagline + "\n\n")
            """

            body = row[bodyI]
            # body = lessHTML(toMarkdown(body, tb=subSubPath))
            body = toMarkdown(body, tb=subSubPath)
            outs.write(body + "\n")

            # outs.write("\n")
            # outs.write("##\n")
            # aside = row[LeftTextI]
            # aside = lessHTML(toMarkdown(aside, tb=subSubPath))
            # outs.write(aside + "\n")

            # outs.write("\n")
            # outs.write("##\n")
            # aside = row[RightTextI]
            # aside = lessHTML(toMarkdown(aside, tb=subSubPath))
            # outs.write(aside + "\n")
            # ^ discard most of them and instead combine them:

        # with open(os.path.splitext(subSub)[0]+"-LeftText.md", 'w') as outs:
        # ^ discard most of them and instead combine them:

        LeftText = stripMore(row[LeftTextI])
        # print("* LeftText was {}".format(row[LeftTextI]))
        if len(LeftText) > 1:  # > on purpose
            extraPath = os.path.join(treePath, "LeftText.md")
            isSideThere = os.path.isfile(extraPath)
            with open(extraPath, 'w') as extraOuts:
                extraOuts.write(LeftText)
            if isSideThere:
                print("* LeftText OVERWROTE {}".format(extraPath))
            else:
                print("* LeftText saved to {}".format(extraPath))

        # print("* RightText was {}".format(row[RightTextI]))
        RightText = stripMore(row[RightTextI]);
        if len(RightText) > 1:  # > on purpose
            extraPath = os.path.join(treePath, "RightText.md")
            isSideThere = os.path.isfile(extraPath)
            with open(extraPath, 'w') as extraOuts:
                extraOuts.write(RightText)
            if isSideThere:
                print("* RightText OVERWROTE {}".format(extraPath))
            else:
                print("* RightText saved to {}".format(extraPath))


treePath = os.path.join(dirPath, "tree-html")
if not os.path.isdir(treePath):
    os.makedirs(treePath)
with open(dest, 'r') as read_obj:
    # pass the file object to reader() to get the reader object
    csv_reader = reader(read_obj)
    # Iterate over each row in the csv using reader object
    for row in csv_reader:
        for i in range(len(row)):
            row[i] = row[i].replace(literalNL, "\n")
        # print("* creating html for {}".format(row[htmlRefI]))
        permaLinkNoExt = os.path.splitext(row[htmlRefI])[0]
        sub = permaLinkNoExt + ".html"
        subSub = sub
        subSubPath = os.path.join(treePath, sub)
        if row[idI] == "0":
            subSubPath = os.path.join(treePath, "index.md")
        elif row[parentI] != "0":
            parentName = parentNames[str(row[parentI])]
            parentPath = os.path.join(treePath, parentName)
            if not os.path.isdir(parentPath):
                os.makedirs(parentPath)
            subSubPath = os.path.join(treePath, parentName, sub)

        print("* creating {}".format(subSubPath))
        with open(subSubPath, 'w') as outs:
            outs.write('<!DOCTYPE html>\n')
            outs.write('<html lang="en-US">\n')
            outs.write('<head>\n')
            outs.write('  <meta charset="UTF-8">\n')
            outs.write('  <title>Streetlight Home</title>\n')
            outs.write('  <meta name="keywords" content="spirituality, street, witnessing, pbu, religion">\n')
            outs.write('  <meta name="description" content="Site for people interested in information about streetlight and spirituality">\n')
            outs.write('  <meta name="rating" content="General">\n')
            outs.write('  <meta name="ROBOTS" content="ALL">\n')
            outs.write('  <meta name="DC.Title" content="Streetlight Home">\n')
            outs.write('  <meta name="DC.Creator" content="Expert Multimedia">\n')
            outs.write('  <meta name="DC.Subject" content="Spirituality">\n')
            outs.write('  <meta name="DC.Description" content="Site for people interested in information about streetlight and spirituality.">\n')
            outs.write('  <meta name="DC.Publisher" content="Expert Multimedia">\n')
            outs.write('  <meta name="author" content="Jake Gustafson">\n')
            outs.write('  <link rel="stylesheet" href="https://streetlightinfo.com/csvedbcms/templates/streetlight1/css/normal1.css" type="text/css"/>\n')
            # outs.write('  \n')
            outs.write('</head>\n')
            outs.write('<body>\n')
            heading, tagline = splitHtmlSubtitle(
                row[shortNameI],
                row[headingAndTaglineI]
            )
            outs.write('  <main>\n')
            outs.write('    <article>\n')
            outs.write('      <header>\n')
            outs.write("        <h2>" + lessHTML(heading) + "</h2>\n")
            # outs.write('        <div class="tagline">\n')
            outs.write("        " + lessHTML(tagline) + "\n")
            # outs.write("        </div>\n")
            outs.write('    </header>\n')
            outs.write(body + "\n")
            outs.write('    </article>\n')
            outs.write("  </main>\n")
            # ^ actually this is unknown, so prepend ~
            outs.write('  <footer>\n')
            outs.write('    <div class="datetime-stamp">\n')
            outs.write("    created: ~{}\n".format(row[updatedI]))
            outs.write("    </div>\n")
            outs.write('    <div class="datetime-stamp">\n')
            outs.write("    updated: {}\n".format(row[updatedI]))
            outs.write('    <div class="tagcloud">\n')
            outs.write('    {}\n'.format(row[TagsI]))
            outs.write('    </div>\n')
            outs.write('  </footer>\n')
            outs.write('  <!-- attrib:{} -->\n'.format(row[AttribI]))
            outs.write('</body>\n')
            outs.write('</html\n')

