# coding: utf-8

# This file is part of the Adblock Plus web scripts,
# Copyright (C) 2006-2015 Eyeo GmbH
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

import jinja2

from ..utils import process_page
from ..sources import FileSource
from ..converters import converters

source = None

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

# Create our own instance, the default one will introduce "random" host-specific
# behavior by parsing local config files.
mime_types = mimetypes.MimeTypes()

def get_data(path):
  if source.has_static(path):
    return source.read_static(path)

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
        return process_page(source, locale, p, format, "http://127.0.0.1:5000")
  if source.has_localizable_file(locale, page):
    return source.read_localizable_file(locale, page)

  return None

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
  if data == None:
    return show_error(start_response, "404 Not Found", uri=path)

  mime = mime_types.guess_type(path)[0] or "text/html"

  if isinstance(data, unicode):
    data = data.encode(UNICODE_ENCODING)
    mime = "%s; charset=%s" % (mime, UNICODE_ENCODING)

  start_response("200 OK", [("Content-Type", mime)])
  return [data]

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print >>sys.stderr, "Usage: %s source_dir" % sys.argv[0]
    sys.exit(1)

  source = FileSource(sys.argv[1])

  try:
    from werkzeug.serving import run_simple
  except ImportError:
    from wsgiref.simple_server import make_server
    def run_simple(host, port, app, **kwargs):
      def wrapper(environ, start_response):
        try:
          return app(environ, start_response)
        except Exception, e:
          return show_error(start_response, "500 Internal Server Error",
              uri=environ.get("PATH_INFO"), error=e)

      server = make_server(host, port, wrapper)
      print " * Running on http://%s:%i/" % server.server_address
      server.serve_forever()

  run_simple("localhost", 5000, handler, use_reloader=True, use_debugger=True)
