# This file is part of the Adblock Plus web scripts,
# Copyright (C) 2006-2016 Eyeo GmbH
#
# Adblock Plus is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# Adblock Plus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adblock Plus.  If not, see <http://www.gnu.org/licenses/>.

import mimetypes
import os
import sys
import argparse

import jinja2

from cms.utils import process_page
from cms.sources import FileSource
from cms.converters import converters

source = None
address = None
port = None

UNICODE_ENCODING = "utf-8"

ERROR_TEMPLATE = """
<html>
  <head>
    <title>{{status}}</title>
  </head>
  <body>
    <h1>{{status}}</h1>
    {% set code = status.split()|first|int %}
    {% if code == 404 %}
      <p>No page found for the address {{uri}}.</p>
    {% elif code == 500 %}
      <p>An error occurred while processing the request for {{uri}}:</p>
      <pre>{{error}}</pre>
    {% endif %}
  </body>
</html>"""

# Initilize the mimetypes modules manually for consistent behavior,
# ignoring local files and Windows Registry.
mimetypes.init([])


def get_page(path):
    path = path.strip("/")
    if path == "":
        path = source.read_config().get("general", "defaultlocale")
    if "/" in path:
        locale, page = path.split("/", 1)
    else:
        locale, page = path, ""

    default_page = source.read_config().get("general", "defaultpage")
    alternative_page = "/".join([page, default_page]).lstrip("/")

    for format in converters.iterkeys():
        for p in (page, alternative_page):
            if source.has_page(p, format):
                return (p, process_page(source, locale, p, format, "http://%s:%d" % (address, port)))
    if source.has_localizable_file(locale, page):
        return (page, source.read_localizable_file(locale, page))

    return (None, None)


def has_conflicting_pages(page):
    pages = [p for p, _ in source.list_pages()]
    pages.extend(source.list_localizable_files())

    if pages.count(page) > 1:
        return True
    if any(p.startswith(page + "/") or page.startswith(p + "/") for p in pages):
        return True
    return False


def get_data(path):
    if source.has_static(path):
        return source.read_static(path)

    page, data = get_page(path)
    if page and has_conflicting_pages(page):
        raise Exception("The requested page conflicts with another page")
    return data


def show_error(start_response, status, **kwargs):
    env = jinja2.Environment(autoescape=True)
    template = env.from_string(ERROR_TEMPLATE)
    mime = "text/html; encoding=%s" % UNICODE_ENCODING
    start_response(status, [("Content-Type", mime)])
    for fragment in template.stream(status=status, **kwargs):
        yield fragment.encode(UNICODE_ENCODING)


def handler(environ, start_response):
    path = environ.get("PATH_INFO")

    data = get_data(path)
    if data is None:
        return show_error(start_response, "404 Not Found", uri=path)

    mime = mimetypes.guess_type(path)[0] or "text/html"

    if isinstance(data, unicode):
        data = data.encode(UNICODE_ENCODING)
        mime = "%s; charset=%s" % (mime, UNICODE_ENCODING)

    start_response("200 OK", [("Content-Type", mime)])
    return [data]

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='CMS development server created to test pages locally and on-the-fly')
    parser.add_argument('path', nargs='?', default=os.curdir)
    parser.add_argument('-a', '--address', default='localhost', help='Address of the interface the server will listen on')
    parser.add_argument('-p', '--port', type=int, default=5000, help='TCP port the server will listen on')
    args = parser.parse_args()

    source = FileSource(args.path)
    address = args.address
    port = args.port

    try:
        from werkzeug.serving import ThreadedWSGIServer, run_simple

        # see https://github.com/mitsuhiko/werkzeug/pull/770
        ThreadedWSGIServer.daemon_threads = True

        def run(*args, **kwargs):
            # The werkzeug logger must be configured before the
            # root logger. Also we must prevent it from propagating
            # messages, otherwise messages are logged twice.
            import logging
            logger = logging.getLogger("werkzeug")
            logger.propagate = False
            logger.setLevel(logging.INFO)
            logger.addHandler(logging.StreamHandler())

            run_simple(threaded=True, *args, **kwargs)
    except ImportError:
        from SocketServer import ThreadingMixIn
        from wsgiref.simple_server import WSGIServer, make_server

        class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
            daemon_threads = True

        def run(host, port, app, **kwargs):
            def wrapper(environ, start_response):
                try:
                    return app(environ, start_response)
                except Exception, e:
                    return show_error(start_response, "500 Internal Server Error",
                                      uri=environ.get("PATH_INFO"), error=e)

            server = make_server(host, port, wrapper, ThreadedWSGIServer)
            print " * Running on http://%s:%i/" % server.server_address
            server.serve_forever()

    run(address, port, handler, use_reloader=True, use_debugger=True)
