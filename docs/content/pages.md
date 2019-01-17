# Pages #

The pages are defined in the `pages` directory. The file extension defines the
format in which a page is specified and won't be visible on the web server.
The page name is prepended by the locale code in the URL, e.g. `pages/foo.md`
can be available under the URLs `/en/foo` and `/de/foo` (the English and German
versions respectively). Regardless of the format, a page can define a number of
settings using the following format:

    setting = value

Note that the settings have to placed at the beginning of the file, before the
actual content.  The following settings can be changed:

* `template`: This defines the template to be used for this page (without the
  file extension). By default the `default` template is used for all pages.
* `title`: The locale string to be used as page title. By default the `title`
  string is used.
* `noheading`: Setting this to any value will make sure no heading is displayed.
  By default a `<h1>` tag with the page title is added above the content.
* `notoc`: Setting this to any value will prevent a table of contents from being
  generated. By default a table of contents is always generated if the page
  contains any headers with an `id` attribute.

For information on using includes on pages, read the guide on
[Include files](includes.md)

## Markdown format (md) ##

This format should normally be used, it allows the pages to be defined using the
[Markdown](http://daringfireball.net/projects/markdown/syntax) syntax. Raw HTML
tags are allowed and can be used where Markdown syntax isn't sufficient. The
[Python-Markdown Extra](https://pythonhosted.org/Markdown/extensions/extra.html)
extension is active and allows specifying custom attributes for the generated
HTML tags, HTML block elements that contain Markdown and more.

Any content between `<head>` and `</head>` tags will be inserted into the head
of the generated web page, this is meant for styles, scripts and the like.
Other pages should be linked by using their name as link target (relative links),
these links will be resolved to point to the most appropriate page language.
Embedding localizable images works the same, use the image name as image source.

Localizable strings can be specified inline with the following syntax:

    {{string_name String contents in default language}}

Try to give the string a descriptive name as it will help translators.
Optionally you can add a description for strings as well to provide even more
context:

    {{string_name[The string description] String contents}}

_Note: String names and descriptions have no effect on the generated page,
assuming string name is unique to the page. The name and description are just
used to provide translators with additional context about the string._

Finally if you find yourself using the same string multiple times in a page
you can reduce duplication by simply omitting the description and contents
after the first use. For example:

    {{title[Title of the page] Adblock Plus - Home}}
    {{title}}

## Raw HTML format (html) ##

This format is similar to the Markdown format but uses regular HTML syntax.
No processing is performed beyond inserting localized strings and resolving
links to pages and images. This format is mainly meant for legacy content.
The syntax for localizable strings documented above can be used as with
Markdown.

## Jinja2 format (tmpl) ##

Complicated pages can be defined using the
[Jinja2 template format](http://jinja.pocoo.org/docs/templates/). Automatic
escaping is active so by default values inserted into the page cannot contain
any HTML code. Any content between `<head>` and `</head>` tags will be inserted
into the head of the generated web page, everything else defined the content of
the page.

Read the API documentation on [variables](../api/variables.md),
[global functions](../api/functions.md), and [custom filters](../api/filters.md)
that can be used on pages.

Prev: [Various include files (`includes`)](includes.md) | Up: [Home](../../README.md) | Next: [Static content (`static`)](static.md)
