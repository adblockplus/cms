# CMS #

We use this CMS for [adblockplus.org](https://github.com/adblockplus/web.adblockplus.org/)
and related websites. It converts a directory with content data into static
files. You are free to use it for other projects but please keep in mind that we
make no stability guarantees whatsoever and might change functionality any time.

## Getting started ##

The easiest way to get started is to run a test server. The test server will 
convert your content directory on the fly, your changes will become visible 
immediately. To run it you need:

* Python 2.7
* [Jinja2](http://jinja.pocoo.org/) and
  [Markdown](https://pypi.python.org/pypi/Markdown) modules (can be installed by
  running `easy_install Jinja2 Markdown` from the command line)
* A current copy of the
  [cms repository](https://github.com/adblockplus/cms/) (can be
  [downloaded as ZIP file](https://github.com/adblockplus/cms/archive/master.zip)
  or cloned via `git clone https://github.com/adblockplus/cms.git`)

Optionally, the [Werkzeug](http://werkzeug.pocoo.org/) module can be installed
as well, this will provide some developer features.

Run the `runserver.py` script from your content directory, e.g.:

    python ../cms/runserver.py

Alternatively, the content directory could also be specified as command line
parameter of `runserver.py`. This will start a local web server on port 5000,
e.g. the page the page `pages/example.md` will be accessible under
`http://localhost:5000/en/example`.

Note that the test server is inefficient and shouldn't be run in production.
There you should generate static files as explained below.

## Documentation ##

- How to use
    - [Running the test server](docs/usage/test-server.md)
    - [Generating the standalone test server](docs/usage/standalone-test-server.md)
    - [Generating static files](docs/usage/generate-static-files.md)
    - [Syncing translations](docs/usage/syncing-translations.md)
    - [XTM Integration](docs/usage/xml-sync.md)
- Content structure
    - [Configuration (`settings.ini`)](docs/content/settings.md)
    - [Custom Jinja2 global functions and variables (`globals`)](docs/content/globals.md)
    - [Custom Jinja2 filters (`filters`)](docs/content/filters.md)
    - [Localization files (`locales`)](docs/content/locales.md)
    - [Page layout templates (`templates`)](docs/content/templates.md)
    - [Various include files (`includes`)](docs/content/includes.md)
    - [User-visible pages (`pages`)](docs/content/pages.md)
    - [Static content (`static`)](docs/content/static.md)
- API
    - [Variables](docs/api/variables.md)
    - [Custom filters](docs/api/filters.md)
    - [Global functions](docs/api/functions.md)
