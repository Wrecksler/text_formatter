# text_formatter

Universal text formatter with support for various formats and specifics of different platforms: Markdown, CF, Discord Markdown, HTML, BBCODE, FList BBCODE, etc

# Example usage

## Print a demo, output given text in all supported formats

```python
    example_markdown = """*some bold text here* and some normal text here and also a [markdown link](https://www.google.com)"""

    TextFormatter.from_markdown(example_bbcode).print_demo()
```

## Convert BBCode to Markdown

```python
    example_bbcode = """Heres a link https://google.com

also some [b]text[/b] on another line"""

    markdown = TextFormatter.from_bbcode(example_bbcode).md
```
