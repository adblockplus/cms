# Global functions #

The following global functions can be used on pages:

* `get_string(name, page=None)`: retrieves a string from a locale file.
  Unless a page is specified the locale file matching the name of the current
  page is used.
* `get_page_content(page, locale=None)`: returns a dictionary of the content
  and params for the given page and locale. Locale defaults to the current one
  if not specified. Provided keys include `head`, `body`, `available_locales`
  and `translation_ratio`.

-----
Prev: [Custom filters](filters.md) | Up: [Home](../../README.md) | Next: [Home](../../README.md)
