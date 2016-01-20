# coding: utf-8

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

import io
import collections
import ConfigParser
import json
import os
from StringIO import StringIO
import subprocess
import urlparse
import zipfile
import logging

class Source:
  def resolve_link(self, url, locale):
    parsed = urlparse.urlparse(url)
    page = parsed.path
    if parsed.scheme != "" or page.startswith("/") or page.startswith("."):
      # Not a page link
      return None, None

    if page == "" and url != "":
      # Page-relative link
      return None, None

    config = self.read_config()
    default_locale = config.get("general", "defaultlocale")
    default_page = config.get("general", "defaultpage")
    alternative_page = "/".join([page.rstrip("/"), default_page]).lstrip("/")

    if self.has_localizable_file(default_locale, page):
      if not self.has_localizable_file(locale, page):
        locale = default_locale
    elif self.has_page(page):
      if not self.has_locale(locale, page):
        locale = default_locale
    elif self.has_page(alternative_page):
      if not self.has_locale(locale, alternative_page):
        locale = default_locale
    else:
      logging.warning("Link to %s cannot be resolved", page)

    parts = page.split("/")
    if parts[-1] == default_page:
      page = "/".join(parts[:-1])

    path = "/%s/%s" % (locale, page)
    return locale, urlparse.urlunparse(parsed[0:2] + (path,) + parsed[3:])

  def read_config(self):
    configdata = self.read_file("settings.ini")[0]
    config = ConfigParser.SafeConfigParser()
    config.readfp(StringIO(configdata))
    return config

  def exec_file(self, filename):
    source, filename = self.read_file(filename)
    code = compile(source, filename, "exec")
    namespace = {}
    exec code in namespace
    return namespace

  #
  # Page helpers
  #

  @staticmethod
  def page_filename(page, format):
    return "pages/%s.%s" % (page, format)

  def list_pages(self):
    for filename in self.list_files("pages"):
      root, ext = os.path.splitext(filename)
      format = ext[1:].lower()
      yield root, format

  def has_page(self, page, format=None):
    if format is None:
      from cms.converters import converters
      return any(
        self.has_page(page, format)
        for format in converters.iterkeys()
      )
    else:
      return self.has_file(self.page_filename(page, format))

  def read_page(self, page, format):
    return self.read_file(self.page_filename(page, format))

  #
  # Localizable files helpers
  #

  @staticmethod
  def localizable_file_filename(locale, filename):
    return "locales/%s/%s" % (locale, filename)

  def list_localizable_files(self):
    default_locale = self.read_config().get("general", "defaultlocale")
    return filter(
      lambda f: os.path.splitext(f)[1].lower() != ".json",
      self.list_files("locales/%s" % default_locale)
    )

  def has_localizable_file(self, locale, filename):
    return self.has_file(self.localizable_file_filename(locale, filename))

  def read_localizable_file(self, locale, filename):
    return self.read_file(self.localizable_file_filename(locale, filename), binary=True)[0]

  #
  # Static file helpers
  #

  @staticmethod
  def static_filename(filename):
    return "static/%s" % filename

  def list_static(self):
    return self.list_files("static")

  def has_static(self, filename):
    return self.has_file(self.static_filename(filename))

  def read_static(self, filename):
    return self.read_file(self.static_filename(filename), binary=True)[0]

  #
  # Locale helpers
  #

  @classmethod
  def locale_filename(cls, locale, page):
    return cls.localizable_file_filename(locale, page + ".json")

  def list_locales(self):
    result = set()
    for filename in self.list_files("locales"):
      if "/" in filename:
        locale, path = filename.split("/", 1)
        result.add(locale)
    return result

  def has_locale(self, locale, page):
    config = self.read_config()
    try:
      page = config.get("locale_overrides", page)
    except ConfigParser.Error:
      pass
    return self.has_file(self.locale_filename(locale, page))

  def read_locale(self, locale, page):
    default_locale = self.read_config().get("general", "defaultlocale")
    result = collections.OrderedDict()
    if locale != default_locale:
      result.update(self.read_locale(default_locale, page))

    if self.has_locale(locale, page):
      filedata = self.read_file(self.locale_filename(locale, page))[0]
      localedata = json.loads(filedata)
      for key, value in localedata.iteritems():
        result[key] = value["message"]

    return result

  #
  # Template helpers
  #

  @staticmethod
  def template_filename(template):
    return "templates/%s.tmpl" % template

  def read_template(self, template):
    return self.read_file(self.template_filename(template))

  #
  # Include helpers
  #

  @staticmethod
  def include_filename(include, format):
    return "includes/%s.%s" % (include, format)

  def has_include(self, include, format):
    return self.has_file(self.include_filename(include, format))

  def read_include(self, include, format):
    return self.read_file(self.include_filename(include, format))

class MercurialSource(Source):
  def __init__(self, repo):
    command = ["hg", "-R", repo, "archive", "-r", "default",
        "-t", "uzip", "-p", ".", "-"]
    data = subprocess.check_output(command)
    self._archive = zipfile.ZipFile(StringIO(data), mode="r")

    command = ["hg", "-R", repo, "id", "-n", "-r", "default"]
    self.version = subprocess.check_output(command).strip()

    self._name = os.path.basename(repo.rstrip(os.path.sep))

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    self.close()
    return False

  def close(self):
    self._archive.close()

  def has_file(self, filename):
    try:
      self._archive.getinfo("./%s" % filename)
    except KeyError:
      return False
    return True

  def read_file(self, filename, binary=False):
    data = self._archive.read("./%s" % filename)
    if not binary:
      data = data.decode("utf-8")
    return (data, "%s!%s" % (self._name, filename))

  def list_files(self, subdir):
    prefix = "./%s/" % subdir
    for filename in self._archive.namelist():
      if filename.startswith(prefix):
        yield filename[len(prefix):]

  if os.name == "posix":
    def get_cache_dir(self):
      return "/var/cache/" + self._name

class FileSource(Source):
  def __init__(self, dir):
    self._dir = dir

  def __enter__(self):
    return self

  def __exit__(self, type, value, traceback):
    return False

  def close(self):
    pass

  def get_path(self, filename):
    return os.path.join(self._dir, *filename.split("/"))

  def has_file(self, filename):
    return os.path.isfile(self.get_path(filename))

  def read_file(self, filename, binary=False):
    path = self.get_path(filename)

    if binary:
      file = open(path, "rb")
    else:
      file = io.open(path, "r", encoding="utf-8")

    with file:
      return (file.read(), path)

  def list_files(self, subdir):
    result = []
    def do_list(dir, relpath):
      try:
        files = os.listdir(dir)
      except OSError:
        return

      for filename in files:
        path = os.path.join(dir, filename)
        if os.path.isfile(path):
          result.append(relpath + filename)
        elif os.path.isdir(path):
          do_list(path, relpath + filename + "/")
    do_list(self.get_path(subdir), "")
    return result

  def get_cache_dir(self):
    return os.path.join(self._dir, "cache")
