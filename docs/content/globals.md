# Custom functions and variables #

The `globals` directory can define custom Jinja2 globals which will be available
in all Jinja2 templates. Typically, this is used for custom functions. The file
name should match the name of the function or variable to be defined, and export
a variable with that name. E.g. `globals/myfunction.py` can define a function
called `myfunction` that will become available to all Jinja2 templates.

-----
Prev: [Configuration (`settings.ini`)](settings.md) | Up: [Home](../../README.md) | Next: [Custom Jinja2 filters (`filters`)](filters.md)
