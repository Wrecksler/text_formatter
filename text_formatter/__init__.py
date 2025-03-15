import bbcode
import markdown
from markdownify import markdownify as md
from markdownify import MarkdownConverter, abstract_inline_conversion
import urllib.parse
import re
from functools import partial
from bs4 import BeautifulSoup
import nh3


def icon(name, value, options, parent, context):
    fmt = {}
    if options:
        fmt.update(options)
    fmt.update({"value": urllib.parse.quote(value.lower())})
    return (
        '<img src="https://static.f-list.net/images/avatar/%(value)s.png" height=50 width=50>'
        % fmt
    )


def collapse(name, collapse_content, options, parent, context):
    """name collapse
    value Some collapsible content
    options {'collapse': 'Collapsible title'}
    parent None
    context {}

    name collapse
    value Some collapsible content without title
    options {}
    parent None
    context {}"""
    title = options.get("collapse", "Click to expand")

    return f"""<details>
<summary>{title}</summary>

{collapse_content}
</details>"""

def heading(name, content, options, parent, context):
    level = options.get("level", "4")

    return f"""<h{int(level)}>{content}</h{int(level)}>"""

def line_all_equal(s, min_length=3):
    if len(s) < min_length:
        return False
    return s == len(s) * s[0]


def markup_strong(node, text, convert_as_inline):
    return f"'''{text}'''"


def markup_em(node, text, convert_as_inline):
    return f"''{text}''"


cf_converter = MarkdownConverter(strong_em_symbol="'", autolinks=False)
cf_converter.convert_b = markup_strong  # abstract_inline_conversion(lambda self: 3 * chatfighters_converter.options['strong_em_symbol'])
cf_converter.convert_strong = cf_converter.convert_b
cf_converter.convert_em = markup_em  # abstract_inline_conversion(lambda this: 2 * this.options['strong_em_symbol'])
cf_converter.convert_i = (
    cf_converter.convert_em
)  # abstract_inline_conversion(lambda this: 2 * this.options['strong_em_symbol'])

md_converter = MarkdownConverter(autolinks=False)

bbcode_parser = bbcode.Parser(
    # replace_links=False
    url_template='<a href="{href}">{text}</a>',
    newline="<br>",
)
bbcode_parser.add_simple_formatter(
    "eicon",
    '<img src="https://static.f-list.net/images/eicon/%(value)s.gif" height=50 width=50>',
)
bbcode_parser.add_formatter("icon", icon)
bbcode_parser.add_simple_formatter("code", "[code]\n%(value)s\n[/code]")
bbcode_parser.add_formatter("collapse", collapse)
bbcode_parser.add_formatter("heading", heading)


def html_to_bbcode(html):
    tags = {
        "b": ("[b]", "[/b]"),
        "strong": ("[b]", "[/b]"),
        "i": ("[i]", "[/i]"),
        "em": ("[i]", "[/i]"),
        "p": ("", ""),
        "u": ("[u]", "[/u]"),
        "s": ("[s]", "[/s]"),
        "eicon": ("[eicon]", "[/eicon]"),
        "icon": ("[icon]", "[/icon]"),
        "code": ("[code]", "[/code]"),
    }

    for tag, bbcode_tags in tags.items():
        html = re.sub(
            rf"<{tag}>(.*?)</{tag}>", rf"{bbcode_tags[0]}\1{bbcode_tags[1]}", html
        )

    html = re.sub(r'<a href="(.*?)">(.*?)</a>', r"[url=\1]\2[/url]", html)

    # Color processing
    html = re.sub(
        r'<span style="color:(.*?);">(.*?)</span>', r"[color=\1]\2[/color]", html
    )

    return html


def bbcode_to_html(bbcode):
    html_processed = ""
    for line in bbcode.split("\n"):
        if line_all_equal(line):
            html_processed += "[hr]\n"
        else:
            html_processed += f"{line}\n"

    # Format
    return bbcode_parser.format(html_processed)


def markdown_to_html(md):
    return markdown.markdown(md)


def cf_to_html(cf_md):
    return markdown_to_html(cf_md.replace("'''", "**").replace("''", "*"))


class TextFormatter:
    supported_in_formats = ["cf", "html", "bbcode", "markdown"]
    supported_out_formats = ["cf", "html", "bbcode", "markdown", "plaintext"]

    def __init__(self, html, safe_html=False, nh3_kwargs={}) -> None:
        self.safe_html = safe_html
        self.nh3_kwargs = nh3_kwargs

        self.html = html

    @property
    def html(self):
        return self._html

    @html.setter
    def html(self, html):
        if self.safe_html:
            html = nh3.clean(html, **self.nh3_kwargs)
        self._html = html

    @classmethod
    def from_bbcode(cls, bbcode, **kwargs):
        html = bbcode_to_html(bbcode)
        return cls(html, **kwargs)

    @classmethod
    def from_html(cls, html, **kwargs):
        return cls(html, **kwargs)

    @classmethod
    def from_markdown(cls, markdown, **kwargs):
        return cls(markdown_to_html(markdown), **kwargs)

    @classmethod
    def from_cf(cls, cf_md, **kwargs):
        return cls(cf_to_html(cf_md), **kwargs)

    @property
    def plaintext(self):
        soup = BeautifulSoup(self.html, features="html.parser")
        return soup.get_text().strip()

    @property
    def markdown(self):
        # return md(self.html).strip()
        raw_md = md_converter.convert(self.html)

        return raw_md

    @property
    def cf(self):
        raw_md = cf_converter.convert(self.html)
        # print(raw_md)
        regex = "\[(?P<url_text>.*?)\]\((?P<url>.*?)\)"
        for match in re.finditer(regex, raw_md, re.MULTILINE):
            url_text = match.group("url_text")
            url = match.group("url")
            if url_text.strip() == url.strip():
                new_link_text = url
            else:
                new_link_text = f"{url_text} ( {url } )"
            raw_md = raw_md.replace(
                match.string[match.start() : match.end()],
                new_link_text,
            )

        # HACK This is temporary solution, must fix these escapes properly
        raw_md = raw_md.replace("\_", "_").replace("\*", "")
        # print (raw_md)
        return raw_md.strip()

    @property
    def discord(self):
        raw_md = self.markdown
        regex = "\[(?P<url_text>.*?)\]\((?P<url>.*?)\)"
        for match in re.finditer(regex, raw_md, re.MULTILINE):
            url_text = match.group("url_text")
            url = match.group("url")
            if url_text.strip() == url.strip():
                new_link_text = url
            else:
                new_link_text = f"{url_text} ( <{url }> )"
            raw_md = raw_md.replace(
                match.string[match.start() : match.end()],
                new_link_text,
            )

        return raw_md.strip()

    @property
    def bbcode(self):
        return html_to_bbcode(self.html).strip()

    def print_demo(self):
        for i in ["html", "plaintext", "bbcode", "markdown", "cf", "discord"]:
            print(f"\n--- {i} ---")
            print(getattr(self, i))


# Testing
if __name__ == "__main__":
    example_markdown = """*some bold text here* and some normal text here and also a [markdown link](https://www.google.com)"""
    example_bbcode = """Heres a link https://google.com

also some [b]text[/b] on another line

[color=red][b]colored bold text[/b][/color]

[collapse=Collapsible title]Some collapsible content[/collapse]

[collapse]Some collapsible content without title[/collapse]


[collapse=Single quotes in arguments ' will break the parser here sadly]
Some content
[/collapse]
"""

    TextFormatter.from_bbcode(example_bbcode).print_demo()
