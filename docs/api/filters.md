# Custom filters #

The following custom filters can be used on pages:

* `translate(default, name, comment=None)`: translates the given default string
   and string name for the current page and locale. The string name should be
   unique for the page but otherwise is only seen by the translators. Optionally
   a comment (description) can be specified to help provide the translators with
   additional context.
* `linkify(url, locale=None, **attrs)`: generates an `<a href="...">` tag for
   the URL. If the URL is a page name it will be converted into a link to the
   most appropriate page language. The language used can also be specified
   manually with the locale parameter. Any further keyword arguments passed
   are turned into additional HTML attributes for the tag.
* `toclist(html)`: extracts a list of headings from HTML code, this can be used
  to generate a table of contents.

-----
Prev: [Variables](variables.md) | Up: [Home](../../README.md) | Next: [Global functions](functions.md)
