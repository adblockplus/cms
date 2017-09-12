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

import os
import re
import errno
import codecs
import ConfigParser
import logging
import subprocess

from argparse import ArgumentParser
from bs4 import BeautifulSoup

from cms.utils import get_page_params, process_page
from cms.sources import create_source

MIN_TRANSLATED = 0.3


def generate_pages(repo, output_dir, revision, version, relative):
    known_files = set()

    def write_file(path_parts, contents, binary=False):
        encoding = None if binary else 'utf-8'
        outfile = os.path.join(output_dir, *path_parts)
        if outfile in known_files:
            logging.warning('File %s has multiple sources', outfile)
            return
        known_files.add(outfile)

        if os.path.exists(outfile):
            with codecs.open(outfile, 'rb', encoding=encoding) as handle:
                if handle.read() == contents:
                    return

        try:
            os.makedirs(os.path.dirname(outfile))
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with codecs.open(outfile, 'wb', encoding=encoding) as handle:
            handle.write(contents)

    with create_source(repo,
                       cached=True,
                       revision=revision,
                       version=version) as source:
        config = source.read_config()
        defaultlocale = config.get('general', 'defaultlocale')
        locales = list(source.list_locales())
        if defaultlocale not in locales:
            locales.append(defaultlocale)

        # First pass: compile the list of pages with given translation level
        def get_locale_file(page):
            try:
                return config.get('locale_overrides', page)
            except ConfigParser.Error:
                return page

        pagelist = set()
        blacklist = set()
        for page, format in source.list_pages():
            for locale in locales:
                if locale == defaultlocale:
                    pagelist.add((locale, page))
                else:
                    params = get_page_params(source, locale, page, format)
                    if params['translation_ratio'] >= MIN_TRANSLATED:
                        pagelist.add((locale, page))
                    else:
                        blacklist.add((locale, get_locale_file(page)))

        # Override existance check to avoid linking to pages we don't generate
        orig_has_locale = source.has_locale

        def has_locale(locale, page):
            page = get_locale_file(page)
            if (locale, page) in blacklist:
                return False
            return orig_has_locale(locale, page)
        source.has_locale = has_locale
        source.resolve_link.cache_clear()

        def rewrite_link(link):
            if link.startswith('/'):
                if source.version:
                    link += '?' + source.version
                if relative:
                    depth = len(page.split('/'))
                    link = '/'.join(['..'] * depth) + link
            return link

        # Second pass: actually generate pages this time
        for locale, page in pagelist:
            pagedata = process_page(source, locale, page)

            root = BeautifulSoup(pagedata, 'html.parser')

            expr = 'img[src], img[srcset], script[src], link[href]'
            for elem in root.select(expr):
                if 'srcset' in elem.attrs:
                    srcset = []
                    for src_zoom in elem.attrs['srcset'].split(', '):
                        try:
                            src, zoom = src_zoom.split(' ')
                        except ValueError:
                            src = src_zoom
                            zoom = None
                        res = rewrite_link(src)
                        if zoom:
                             res = res + ' ' + zoom
                        srcset.append(res)

                    elem.attrs['srcset'] = ', '.join(srcset)

                for key in ['src', 'href']:
                    if key in elem.attrs:
                        elem.attrs[key] = rewrite_link(elem.attrs[key])

            pagedata = root.prettify()

            write_file([locale] + page.split('/'), pagedata)

        for filename in source.list_localizable_files():
            for locale in locales:
                if source.has_localizable_file(locale, filename):
                    filedata = source.read_localizable_file(locale, filename)
                    write_file([locale] + filename.split('/'), filedata, binary=True)

        for filename in source.list_static():
            write_file(filename.split('/'), source.read_static(filename), binary=True)

    def remove_unknown(dir):
        files = os.listdir(dir)
        for filename in files:
            path = os.path.join(dir, filename)
            if os.path.isfile(path) and path not in known_files:
                os.remove(path)
            elif os.path.isdir(path):
                remove_unknown(path)
                if not os.listdir(path):
                    os.rmdir(path)
    remove_unknown(output_dir)


if __name__ == '__main__':
    parser = ArgumentParser('Convert website source to static website')
    parser.add_argument('-r', '--rev',
                        help='Specify which revision to generate from. '
                             'See "hg help revisions" for details.',
                        default='default')
    parser.add_argument('-v', '--version', default=None,
                        help=('Specify the version string to be used if you '
                              'generating from a FileSource. Only pass REV or '
                              'VERSION not both'))

    parser.add_argument('--relative', action='store_true', default=False)
    parser.add_argument('source', help="Path to website's repository")
    parser.add_argument('output', help='Path to desired output directory')
    args = parser.parse_args()

    if args.version and args.rev != 'default':
        raise parser.error('Cannot specify rev and version at the same time')
    elif args.version:
        args.rev = None

    generate_pages(args.source, args.output, args.rev, args.version, args.relative)
