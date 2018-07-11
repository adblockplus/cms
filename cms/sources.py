# This file is part of the Adblock Plus web scripts,
# Copyright (C) 2006-present eyeo GmbH
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
from random import randint
import urlparse
import logging


class Source:
    def resolve_link(self, url, locale):
        parsed = urlparse.urlparse(url)
        page = parsed.path
        if parsed.scheme != '' or page.startswith('/') or page.startswith('.'):
            # Not a page link
            return None, None

        if url.startswith('tel:'):
            # Workaround for 'tel' scheme not recognized in Python <=2.7.3.
            return None, None

        if page == '' and url != '':
            # Page-relative link
            return None, None

        config = self.read_config()
        default_locale = config.get('general', 'defaultlocale')
        default_page = config.get('general', 'defaultpage')
        alternative_page = '/'.join([page.rstrip('/'), default_page]).lstrip('/')

        if self.has_localizable_file(default_locale, page):
            if not self.has_localizable_file(locale, page):
                locale = default_locale
        elif self.has_page(page):
            if not self.has_locale(locale, page):
                locale = default_locale
        elif self.has_page(alternative_page):
            if not self.has_locale(locale, alternative_page):
                locale = default_locale
        elif self.has_static(page):
            locale = None
        else:
            logging.warning('Link to %s cannot be resolved', page)

        parts = page.split('/')
        if parts[-1] == default_page:
            page = '/'.join(parts[:-1])
        if locale:
            path = '/{}/{}'.format(locale, page)
            return locale, urlparse.urlunparse(parsed[0:2] + (path,) + parsed[3:])
        return locale, '/' + page

    def read_config(self):
        configdata = self.read_file('settings.ini')[0]
        config = ConfigParser.SafeConfigParser()
        config.readfp(StringIO(configdata))
        return config

    def exec_file(self, filename):
        source, filename = self.read_file(filename)
        code = compile(source, filename, 'exec')
        namespace = {}
        exec code in namespace
        return namespace

    #
    # Page helpers
    #

    @staticmethod
    def page_filename(page, format):
        return 'pages/%s.%s' % (page, format)

    def list_pages(self):
        for filename in self.list_files('pages'):
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
        return 'locales/%s/%s' % (locale, filename)

    def list_localizable_files(self):
        default_locale = self.read_config().get('general', 'defaultlocale')
        return filter(lambda f: os.path.splitext(f)[1].lower() != '.json',
                      self.list_files('locales/%s' % default_locale))

    def has_localizable_file(self, locale, filename):
        return self.has_file(self.localizable_file_filename(locale, filename))

    def read_localizable_file(self, locale, filename):
        return self.read_file(self.localizable_file_filename(locale, filename), binary=True)[0]

    #
    # Static file helpers
    #

    @staticmethod
    def static_filename(filename):
        return 'static/%s' % filename

    def list_static(self):
        return self.list_files('static')

    def has_static(self, filename):
        return self.has_file(self.static_filename(filename))

    def read_static(self, filename):
        return self.read_file(self.static_filename(filename), binary=True)[0]

    #
    # Locale helpers
    #

    def locale_filename(self, locale, page):
        config = self.read_config()
        try:
            page = config.get('locale_overrides', page)
        except ConfigParser.Error:
            pass
        return self.localizable_file_filename(locale, page + '.json')

    def list_locales(self):
        result = set()
        for filename in self.list_files('locales'):
            if '/' in filename:
                locale, path = filename.split('/', 1)
                result.add(locale)
        return result

    def has_locale(self, locale, page):
        return self.has_file(self.locale_filename(locale, page))

    def read_locale(self, locale, page):
        default_locale = self.read_config().get('general', 'defaultlocale')
        result = collections.OrderedDict()
        if locale != default_locale:
            result.update(self.read_locale(default_locale, page))

        if self.has_locale(locale, page):
            filename = self.locale_filename(locale, page)
            filedata, filepath = self.read_file(filename)
            try:
                localedata = json.loads(filedata)
                for key, value in localedata.iteritems():
                    result[key] = value['message']
            except KeyError as ke:
                if ke.message != 'message':
                    raise
                raise ValueError('The content of translations file for page '
                                 '"{}", language "{}" ({}) is not a valid '
                                 'translations file: "message" key is missing '
                                 'for string: "{}"'.format(page, locale,
                                                           filepath, key))
            except (AttributeError, ValueError):
                raise ValueError('The content of translations file for page '
                                 '"{}", language "{}" ({}) is not a valid '
                                 'JSON object'.format(page, locale, filepath))

        return result

    #
    # Template helpers
    #

    @staticmethod
    def template_filename(template):
        return 'templates/%s.tmpl' % template

    def read_template(self, template):
        return self.read_file(self.template_filename(template))

    #
    # Include helpers
    #

    @staticmethod
    def include_filename(include, format):
        return 'includes/%s.%s' % (include, format)

    def has_include(self, include, format):
        return self.has_file(self.include_filename(include, format))

    def read_include(self, include, format):
        return self.read_file(self.include_filename(include, format))


class FileSource(Source):
    def __init__(self, dir):
        self._dir = dir

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return False

    def close(self):
        pass

    @property
    def version(self):
        return randint(1, 2 ** 32)

    def get_path(self, filename):
        return os.path.join(self._dir, *filename.split('/'))

    def has_file(self, filename):
        return os.path.isfile(self.get_path(filename))

    def read_file(self, filename, binary=False):
        path = self.get_path(filename)

        if binary:
            file = open(path, 'rb')
        else:
            file = io.open(path, 'r', encoding='utf-8')

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
                    do_list(path, relpath + filename + '/')
        do_list(self.get_path(subdir), '')
        return result

    def get_cache_dir(self):
        return os.path.join(self._dir, 'cache')


class MultiSource(Source):
    """A source that combines the contents of multiple other sources."""

    def __init__(self, base_sources):
        self._bases = base_sources

    @property
    def version(self):
        return self._bases[0].version

    def get_cache_dir(self):
        return self._bases[0].get_cache_dir()

    def __enter__(self):
        for base in self._bases:
            base.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        return any(base.__exit__(exc_type, exc_value, tb)
                   for base in self._bases)

    def close(self):
        for base in self._bases:
            base.close()

    def has_file(self, filename):
        return any(base.has_file(filename) for base in self._bases)

    def read_file(self, filename, binary=False):
        for base in self._bases:
            if base.has_file(filename):
                return base.read_file(filename, binary)
        raise KeyError('File not found {}'.format(filename))

    def list_files(self, subdir):
        return {f for base in self._bases for f in base.list_files(subdir)}

    def list_pages(self):
        # We can't let the base class implementation of `list_pages` handle
        # this on top of `list_files` because the same page can have multiple
        # possible source files. When those source files reside in different
        # base sources, only the first of them should be visible. Possible
        # source files of the page in later sources should be shadowed to avoid
        # unexpected conflicts.
        all_seen = set()
        for base in self._bases:
            base_seen = set()
            for page, ext in base.list_pages():
                if page not in all_seen:
                    yield page, ext
                    base_seen.add(page)
            all_seen.update(base_seen)

    def has_page(self, page, format=None):
        # This function has to behave consistently with `list_pages` so we must
        # check if the page (in any format) exists in earlier bases before we
        # check later ones.
        for base in self._bases:
            if base.has_page(page):
                if format is None:
                    return True
                # If a page exists in an earlier base in another format than
                # requested, it will shadow the same page in later bases.
                # Therefore, as as soon as we find a base that has the page in
                # any format, we can delegate to it completely.
                return base.has_page(page, format)
        else:
            return False


def _memoize(func):
    """Cache results of functions calls."""
    memoized = {}

    def wrapper(*args):
        try:
            return memoized[args]
        except KeyError:
            return memoized.setdefault(args, func(*args))
    wrapper.cache_clear = memoized.clear
    return wrapper


def create_source(path, cached=False):
    """Create a source from path.

    `cached` flag activates caching. This can be used to optimize performance
    if no changes are expected on the filesystem after the source was created.
    This is usually the case with static generation (as opposed to dynamic
    preview).

    If `settings.ini` in the source contains `[paths]` section with an
    `additional-paths` key that contains the list of additional root folders,
    `MultiSource` will be instantiated and its bases will be the original
    source plus an additional source for each additional root folder.
    `MultiSource` looks up files in its base sources in the order they are
    provided, so the files in the additional folders will only be used if the
    original source doesn't contain that file.
    """
    source = FileSource(path)

    config = source.read_config()
    try:
        ap = config.get('paths', 'additional-paths').strip()
        additional_paths = filter(None, ap.split())
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        additional_paths = []

    if additional_paths:
        additional_sources = [
            create_source(os.path.join(path, p))
            for p in additional_paths
        ]
        source = MultiSource([source] + additional_sources)

    if cached:
        for fname in [
            'resolve_link',
            'read_config',
            'read_template',
            'read_locale',
            'read_include',
            'exec_file',
        ]:
            setattr(source, fname, _memoize(getattr(source, fname)))

    return source
