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

import os
import HTMLParser
import re

import jinja2
import markdown


# Monkey-patch Markdown's isBlockLevel function to ensure that no paragraphs
# are inserted into the <head> tag
orig_isBlockLevel = markdown.util.isBlockLevel


def isBlockLevel(tag):
    if tag == 'head':
        return True
    return orig_isBlockLevel(tag)

markdown.util.isBlockLevel = isBlockLevel

html_escapes = {
    '<': '&lt;',
    '>': '&gt;',
    '&': '&amp;',
    '"': '&quot;',
    "'": '&#39;',
}


class AttributeParser(HTMLParser.HTMLParser):
    _string = None
    _inside_fixed = False
    _fixed_strings = None
    _attrs = None

    def __init__(self, whitelist):
        self._whitelist = whitelist

    def parse(self, text, pagename):
        self.reset()
        self._string = []
        self._fixed_strings = []
        self._inside_fixed = False
        self._attrs = {}
        self._pagename = pagename

        # Force-escape ampersands, otherwise the parser will autocomplete bogus
        # entities.
        text = re.sub(r'&(?!\S+;)', '&amp;', text)

        try:
            self.feed(text)
            return (''.join(self._string),
                    self._attrs, [''.join(s) for s in self._fixed_strings])
        finally:
            self._string = None
            self._attrs = None
            self._pagename = None
            self._inside_fixed = False
            self._fixed_strings = None

    def handle_starttag(self, tag, attrs):
        if self._inside_fixed:
            raise Exception("Unexpected HTML tag '{}' inside a fixed string"
                            'on page {}'.format(tag, self._pagename))
        if tag == 'fix':
            self._inside_fixed = True
            self._fixed_strings.append([])
        if tag in self._whitelist:
            self._attrs.setdefault(tag, []).append(attrs)
            self._string.append('<{}>'.format(tag))
        else:
            raise Exception("Unexpected HTML tag '{}' inside a fixed string"
                            'on page {}'.format(tag, self._pagename))

    def handle_endtag(self, tag):
        if tag == 'fix':
            self._string.append('{{{}}}'.format(self._fixed_strings))
            self._inside_fixed = False
        else:
            self._string.append('</{}>'.format(tag))

    def _append_text(self, s):
        if self._inside_fixed:
            self._fixed_strings[-1].append(s)
        else:
            self._string.append(s)

    def handle_data(self, data):
        # Note: lack of escaping here is intentional. The result is a locale
        # string, HTML escaping is applied when this string is inserted into
        # the document.
        self._append_text(data)

    def handle_entityref(self, name):
        self._append_text(self.unescape('&{};'.format(name)))

    def handle_charref(self, name):
        self._append_text(self.unescape('&#{};'.format(name)))


class Converter:
    whitelist = {'a', 'em', 'sup', 'strong', 'code', 'span'}
    missing_translations = 0
    total_translations = 0

    def __init__(self, params, key='pagedata'):
        self._params = params
        self._key = key
        self._attribute_parser = AttributeParser(self.whitelist)
        self._seen_defaults = {}

        # Read in any parameters specified at the beginning of the file
        data, filename = params[key]
        lines = data.splitlines(True)
        for i, line in enumerate(lines):
            if not re.search(r'^\s*[\w\-]+\s*=', line):
                break
            name, value = line.split('=', 1)
            params[name.strip()] = value.strip()
            lines[i] = '\n'
        params[key] = (''.join(lines), filename)

    def localize_string(
            self, page, name, default, comment, localedata, escapes):

        def escape(s):
            return re.sub(r'.',
                          lambda match: escapes.get(match.group(0),
                                                    match.group(0)),
                          s, flags=re.S)

        def re_escape(s):
            return re.escape(escape(s))

        # Handle duplicated strings
        if default:
            self._seen_defaults[(page, name)] = (default, comment)
        else:
            try:
                default, comment = self._seen_defaults[(page, name)]
            except KeyError:
                raise Exception('Text not yet defined for string {} on page'
                                '{}'.format(name, page))

        # Extract tag attributes from default string
        default, saved_attributes, fixed_strings = (
            self._attribute_parser.parse(default, self._params['page']))

        # Get translation
        locale = self._params['locale']
        if locale == self._params['defaultlocale']:
            result = default
        elif name in localedata:
            result = localedata[name].strip()
        else:
            result = default
            self.missing_translations += 1
        self.total_translations += 1

        # Perform callback with the string if required, e.g. for the
        # translations script
        callback = self._params['localized_string_callback']
        if callback:
            callback(page, locale, name, result, comment, fixed_strings)

        # Insert fixed strings
        for i, fixed_string in enumerate(fixed_strings, 1):
            result = result.replace('{{{%d}}}'.format(i), fixed_string)

        # Insert attributes
        result = escape(result)

        def stringify_attribute((name, value)):
            return '{}="{}"'.format(
                escape(name),
                escape(self.insert_localized_strings(value, {}))
            )

        for tag in self.whitelist:
            allowed_contents = '(?:[^<>]|{})'.format('|').join((
                '<(?:{}[^<>]*?|/{})>'.format(t, t)
                for t in map(re.escape, self.whitelist - {tag})
            ))
            saved = saved_attributes.get(tag, [])
            for attrs in saved:
                attrs = map(stringify_attribute, attrs)
                result = re.sub(
                    r'{}({}*?){}'.format(re_escape('<{}>'.format(tag)),
                                         allowed_contents,
                                         re_escape('</{}>'.format(tag))),
                    lambda match: r'<{}{}>{}</{}>'.format(
                        tag,
                        ' ' + ' '.join(attrs) if attrs else '',
                        match.group(1),
                        tag
                    ),
                    result, 1, flags=re.S
                )
            result = re.sub(
                r'{}({}*?){}'.format(re_escape('<{}>'.format(tag)),
                                     allowed_contents,
                                     re_escape('</{}>'.format(tag))),
                r'<{}>\1</{}>'.format(tag, tag),
                result, flags=re.S
            )
        return result

    def insert_localized_strings(self, text, escapes, to_html=lambda s: s):
        def lookup_string(match):
            name, comment, default = match.groups()
            if default:
                default = to_html(default).strip()
            return self.localize_string(self._params['page'], name, default,
                                        comment, self._params['localedata'],
                                        escapes)

        return re.sub(
            r'{{\s*'
            r'([\w\-]+)'  # String ID
            r'(?:(?:\[(.*?)\])?'  # Optional comment
            r'\s+'
            r'((?:(?!{{).|'  # Translatable text
            r'{{(?:(?!}}).)*}}'  # Nested translation
            r')*?)'
            r')?'
            r'}}',
            lookup_string,
            text,
            flags=re.S
        )

    def process_links(self, text):
        def process_link(match):
            pre, attr, url, post = match.groups()
            url = jinja2.Markup(url).unescape()

            locale, new_url = (
                self._params['source']
                .resolve_link(url, self._params['locale']))

            if new_url is not None:
                url = new_url
                if attr == 'href':
                    post += ' hreflang="{}"'\
                        .format(jinja2.Markup.escape(locale))

            return ''.join((pre, jinja2.Markup.escape(url), post))

        text = re.sub(r'(<a\s[^<>]*\b(href)=\")([^<>\"]+)(\")',
                      process_link, text)
        text = re.sub(r'(<img\s[^<>]*\b(src)=\")([^<>\"]+)(\")',
                      process_link, text)
        return text

    include_start_regex = '<'
    include_end_regex = '>'

    def resolve_includes(self, text):
        def resolve_include(match):
            name = match.group(1)
            for format_, converter_class in converters.iteritems():
                if self._params['source'].has_include(name, format_):
                    self._params['includedata'] = (
                        self._params['source'].read_include(name, format_))

                    converter = converter_class(self._params,
                                                key='includedata')
                    result = converter()
                    self.missing_translations += converter.missing_translations
                    self.total_translations += converter.total_translations
                    return result
            raise Exception('Failed to resolve include {}'
                            'on page {}'.format(name, self._params['page']))

        return re.sub(
            r'{}\?\s*include\s+([^\s<>"]+)\s*\?{}'.format(
                self.include_start_regex,
                self.include_end_regex
            ),
            resolve_include,
            text
        )

    def __call__(self):
        result = self.get_html(*self._params[self._key])
        result = self.resolve_includes(result)
        if self._key == 'pagedata':
            head = []

            def add_to_head(match):
                head.append(match.group(1))
                return ''
            body = re.sub(r'<head>(.*?)</head>', add_to_head, result,
                          flags=re.S)
            return ''.join(head), body
        return result


class RawConverter(Converter):
    def get_html(self, source, filename):
        result = self.insert_localized_strings(source, html_escapes)
        result = self.process_links(result)
        return result


class MarkdownConverter(Converter):
    include_start_regex = r'(?:{}|{})'.format(
        Converter.include_start_regex,
        re.escape(jinja2.escape(Converter.include_start_regex))
    )
    include_end_regex = r'(?:{}|{})'.format(
        Converter.include_end_regex,
        re.escape(jinja2.escape(Converter.include_end_regex))
    )

    def get_html(self, source, filename):
        def remove_unnecessary_entities(match):
            char = unichr(int(match.group(1)))
            if char in html_escapes:
                return match.group(0)
            return char

        escapes = {}
        md = markdown.Markdown(output='html5', extensions=['extra'])
        for char in md.ESCAPED_CHARS:
            escapes[char] = '&#{};'.format(str(ord(char)))
        for key, value in html_escapes.iteritems():
            escapes[key] = value

        md.preprocessors['html_block'].markdown_in_raw = True

        def to_html(s):
            return re.sub(r'</?p>', '', md.convert(s))

        result = self.insert_localized_strings(source, escapes, to_html)
        result = md.convert(result)
        result = re.sub(r'&#(\d+);', remove_unnecessary_entities, result)
        result = self.process_links(result)
        return result


class SourceTemplateLoader(jinja2.BaseLoader):
    def __init__(self, source):
        self.source = source

    def get_source(self, environment, template):
        try:
            result = self.source.read_file(template + '.tmpl')
        except Exception:
            raise jinja2.TemplateNotFound(template)
        return result + (None,)


class TemplateConverter(Converter):
    def __init__(self, *args, **kwargs):
        Converter.__init__(self, *args, **kwargs)

        filters = {
            'translate': self.translate,
            'linkify': self.linkify,
            'toclist': self.toclist,
        }

        globals = {
            'get_string': self.get_string,
            'get_page_content': self.get_page_content,
        }

        for dirname, dictionary in [('filters', filters),
                                    ('globals', globals)]:
            for filename in self._params['source'].list_files(dirname):
                root, ext = os.path.splitext(filename)
                if ext.lower() != '.py':
                    continue

                path = os.path.join(dirname, filename)
                namespace = self._params['source'].exec_file(path)

                name = os.path.basename(root)
                try:
                    dictionary[name] = namespace[name]
                except KeyError:
                    raise Exception('Expected symbol {} not found'
                                    'in {}'.format(name, path))

        self._env = jinja2.Environment(
            loader=SourceTemplateLoader(self._params['source']),
            autoescape=True)
        self._env.filters.update(filters)
        self._env.globals.update(globals)

    def get_html(self, source, filename):
        env = self._env
        code = env.compile(source, None, filename)
        template = jinja2.Template.from_code(env, code, env.globals)

        try:
            module = template.make_module(self._params)
        except Exception:
            env.handle_exception()

        for key, value in module.__dict__.iteritems():
            if not key.startswith('_'):
                self._params[key] = value

        result = unicode(module)
        result = self.process_links(result)
        return result

    def translate(self, default, name, comment=None):
        return jinja2.Markup(self.localize_string(
            self._params['page'], name, default, comment,
            self._params['localedata'], html_escapes
        ))

    def get_string(self, name, page=None):
        if page is None:
            page = self._params['page']

        localedata = self._params['source'].read_locale(self._params['locale'],
                                                        page)
        default = localedata[name]
        return jinja2.Markup(self.localize_string(
            page, name, default, '', localedata, html_escapes
        ))

    def get_page_content(self, page, locale=None):
        from cms.utils import get_page_params

        if locale is None:
            locale = self._params['locale']
        return get_page_params(self._params['source'], locale, page)

    def linkify(self, page, locale=None, **attrs):
        if locale is None:
            locale = self._params['locale']

        locale, url = self._params['source'].resolve_link(page, locale)
        return jinja2.Markup('<a{}>'.format(''.join(
            ' {}="{}"'.format(name, jinja2.escape(value)) for name, value in [
                ('href', url),
                ('hreflang', locale)
            ] + attrs.items()
        )))

    def toclist(self, content):
        toc_re = r'<h(\d)\s[^<>]*\bid="([^<>"]+)"[^<>]*>(.*?)</h\1>'
        flat = []
        for match in re.finditer(toc_re, content, re.S):
            flat.append({
                'level': int(match.group(1)),
                'anchor': jinja2.Markup(match.group(2)).unescape(),
                'title': jinja2.Markup(match.group(3)).unescape(),
                'subitems': [],
            })

        structured = []
        stack = [{'level': 0, 'subitems': structured}]
        for item in flat:
            while stack[-1]['level'] >= item['level']:
                stack.pop()
            stack[-1]['subitems'].append(item)
            stack.append(item)
        return structured

converters = {
    'html': RawConverter,
    'md': MarkdownConverter,
    'tmpl': TemplateConverter,
}
