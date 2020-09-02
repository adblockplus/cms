# Generating static files #

On your production server you should convert the content directory into static
files. To do that you need:

* Python 3.7
* [Jinja2](http://jinja.pocoo.org/) and
  [Markdown](https://pypi.python.org/pypi/Markdown) modules (can be installed by
  running `easy_install Jinja2 Markdown` from the command line)
* A current copy of the
  [cms-py3 branch](https://gitlab.com/eyeo/websites/cms/-/tree/cms-py3) (can be
  cloned via `git clone https://gitlab.com/eyeo/websites/cms --branch cms-py3 --single-branch`)

Run the following command from the directory of the `cms` repository:

    python -m cms.bin.generate_static_pages www_directory target_directory

Here `www_directory` should be replaced by the path to your content directory.
`target_directory` is the path where static files will be placed.

The files can also be generated with relative links instead of asolute links by
using the `--relative` option:

    python -m cms.bin.generate_static_pages www_directory target_directory --relative

Note: Localized versions of pages will only be generated when their translations
are at least 30% complete. (Measured by comparing the total number
of translatable strings on a page to the number of strings that have been
translated for a given locale.) This is different from the test server which
will include less complete translations.

-----
Prev: [Generating the standalone test server](standalone-test-server.md) | Up: [Home](../../README.md) | Next: [Syncing translations](syncing-translations.md)
