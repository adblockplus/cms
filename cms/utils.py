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

import re

__all__ = [
    'get_page_params',
    'process_page',
    'split_head_body',
    'extract_page_metadata',
]


def split_head_body(html):
    """Split HTML page into head and remaining content.

    This is used to pass head and body of the page to the template as two
    separate variables.

    Parameters
    ----------
    html: str
        Source HTML to split.

    Returns
    -------
    (str, str)
        Everything inside of <head> tags found in the page,
        the rest of the page text with <head> tags removed.

    """
    head = []

    def add_to_head(match):
        head.append(match.group(1))
        return ''

    body = re.sub(r'<head>(.*?)</head>', add_to_head, html, flags=re.S)
    return ''.join(head), body


def extract_page_metadata(source):
    """Extract metadata variables from source text of the page.

    Parameters
    ----------
    source: str
        Source text of the page.

    Returns
    -------
    (dict, str)
        Metadata of the page, remaining source text without metadata.

    """
    metadata = {}
    lines = source.splitlines(True)
    for i, line in enumerate(lines):
        if line.strip() in {'<!--', '-->'}:
            lines[i] = ''
            continue
        if not re.search(r'^\s*[\w\-]+\s*=', line):
            break
        name, value = line.split('=', 1)
        value = value.strip()
        if value.startswith('[') and value.endswith(']'):
            value = [element.strip() for element in value[1:-1].split(',')]
        lines[i] = '\n'
        metadata[name.strip()] = value
    return metadata, ''.join(lines)


def get_page_params(source, locale, page, format=None, site_url_override=None,
                    localized_string_callback=None):
    from cms.converters import converters

    # Guess page format if omitted, but default to Markdown for friendlier exceptions
    if format is None:
        for format in converters.iterkeys():
            if source.has_page(page, format):
                break
        else:
            format = 'md'

    params = {
        'source': source,
        'template': 'default',
        'locale': locale,
        'page': page,
        'config': source.read_config(),
        'localized_string_callback': localized_string_callback,
    }

    localefile = page
    if params['config'].has_option('locale_overrides', page):
        localefile = params['config'].get('locale_overrides', page)
    params['localedata'] = source.read_locale(params['locale'], localefile)

    if params['config'].has_option('general', 'siteurl'):
        if site_url_override:
            params['site_url'] = site_url_override
        else:
            params['site_url'] = params['config'].get('general', 'siteurl')

    data, filename = source.read_page(page, format)
    metadata, body = extract_page_metadata(data)
    params['pagedata'] = body, filename
    params.update(metadata)

    params['templatedata'] = source.read_template(params['template'])

    defaultlocale = params['config'].get('general', 'defaultlocale')
    params['defaultlocale'] = defaultlocale

    locales = [
        l
        for l in source.list_locales()
        if source.has_locale(l, localefile)
    ]
    if defaultlocale not in locales:
        locales.append(defaultlocale)
    locales.sort()
    params['available_locales'] = locales

    try:
        converter_class = converters[format]
    except KeyError:
        raise Exception('Page %s uses unknown format %s' % (page, format))

    converter = converter_class(body, filename, params)
    converted = converter()
    params['head'], params['body'] = split_head_body(converted)

    if converter.total_translations > 0:
        params['translation_ratio'] = (
            1 - float(converter.missing_translations) / converter.total_translations
        )
    else:
        params['translation_ratio'] = 1

    return params


def process_page(source, locale, page, format=None, site_url_override=None,
                 localized_string_callback=None):
    from cms.converters import TemplateConverter

    params = get_page_params(source, locale, page, format, site_url_override,
                             localized_string_callback)
    return TemplateConverter(*params['templatedata'], params=params)()
