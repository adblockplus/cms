# Templates #

The templates specified in the `templates` directory specify the overall
structure that is common for all pages. These templates should have the file
extension `tmpl` and use the [Jinja2 template format](http://jinja.pocoo.org/docs/templates/).
The differences to pages using the same format are:

* No special treatment of the `<head>` tag.
* Additional variables `head` and `body` are defined with the HTML code that
  should be added to the head and content of the page respectively.

By default, `default.tmpl` will be used for all pages. If other templates are
defined, the pages need to choose them explicitly using the `template` setting.

-----
Prev: [Localization files (`locales`)](locales.md) | Up: [Home](../../README.md) | Next: [Various include files (`includes`)](includes.md)
