# Running the test server #

The test server will convert your content directory on the fly, your changes
will become visible immediately. To run it you need:

* Python 3.7
* [Jinja2](http://jinja.pocoo.org/) and
  [Markdown](https://pypi.python.org/pypi/Markdown) modules (can be installed by
  running `easy_install Jinja2 Markdown` from the command line)
* A current copy of the
  [cms-py3 branch](https://gitlab.com/eyeo/websites/cms/-/tree/cms-py3) (can be
  cloned via `git clone https://gitlab.com/eyeo/websites/cms --branch cms-py3 --single-branch`)


Optionally, the [Werkzeug](http://werkzeug.pocoo.org/) module can be installed
as well, this will provide some developer features.

Run the `runserver.py` script from your content directory, e.g.:

    python ../cms/runserver.py

Alternatively, the content directory could also be specified as command line
parameter of `runserver.py`. This will start a local web server on port 5000,
e.g. the page the page `pages/example.md` will be accessible under
`http://localhost:5000/en/example`.

Note that the test server is inefficient and shouldn't be run in production.
There you should generate static files as explained in the next guide,
[Generating Static Files](generate-static-files.md).

-----
Prev: [Home](../../README.md) | Up: [Home](../../README.md) | Next: [Generating the standalone test server](standalone-test-server.md)
