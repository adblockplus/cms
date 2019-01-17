# Global functions #

The following global functions can be used on pages:

* `get_string(name, page=None)`: retrieves a string from a locale file.
  Unless a page is specified the locale file matching the name of the current
  page is used.
* `has_string(name, page=None)`: returns true if the named string exists in
  the speficied page, otherwise returns false. If no page is specified, the
  locale file matching the name of the current page if used.
* `get_page_content(page, locale=None)`: returns a dictionary of the content
  and params for the given page and locale. Locale defaults to the current one
  if not specified. Provided keys include `head`, `body`, `available_locales`
  and `translation_ratio`.
* `get_pages_metadata(filters=None)`: returns the metadata for all pages, if
  no filters are given. If a filter is given, returns the metadata for each
  page that matches the filter. Filters should be dictionaries. E.g.
  `get_pages_metadata({'tags': ['popular', 'bar']})`
* `get_canonical_url(page)`: returns the canonical URL for the given page,
  without the locale code. The base URL must be configured in `settings.ini`
  as `siteurl`.

Prev: [Custom filters](filters.md) | Up: [Home](../../README.md) | Next: [Home](../../README.md)
