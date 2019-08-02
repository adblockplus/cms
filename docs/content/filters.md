# Custom filters #

The `filters` directory can define custom Jinja2 filters which will be available
in all Jinja2 templates. The file name defines the filter name, e.g.
`filters/myfilter.py` will define a filter named `myfilter`. This file should
also contain a function called `myfilter`, this one will be called when the
filter is invoked. For more information on Jinja2 filters see
[official documentation](http://jinja.pocoo.org/docs/dev/api/#writing-filters).

-----
Prev: [Custom Jinja2 global functions and variables (`globals`)](globals.md) | Up: [Home](../../README.md) | Next: [Localization files (`locales`)](locales.md)
