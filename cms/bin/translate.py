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

import codecs
import collections
import io
import itertools
import json
import logging
import os
import posixpath
import sys
import urllib
import zipfile

import urllib3

import cms.utils
from cms.sources import FileSource

logger = logging.getLogger('cms.bin.translate')


class CrowdinAPI:
    FILES_PER_REQUEST = 20

    def __init__(self, api_key, project_name):
        self.api_key = api_key
        self.project_name = project_name
        self.connection = urllib3.connection_from_url('https://api.crowdin.com/')

    def raw_request(self, request_method, api_endpoint, query_params=(), **kwargs):
        url = '/api/project/%s/%s?%s' % (
            urllib.quote(self.project_name),
            urllib.quote(api_endpoint),
            urllib.urlencode((('key', self.api_key),) + query_params),
        )
        try:
            response = self.connection.request(
                request_method, str(url), **kwargs
            )
        except urllib3.exceptions.HTTPError:
            logger.error('Connection to API endpoint %s failed', url)
            raise
        if response.status < 200 or response.status >= 300:
            logger.error('API call to %s failed:\n%s', url, response.data)
            raise urllib3.exceptions.HTTPError(response.status)
        return response

    def request(self, request_method, api_endpoint, data=None, files=None):
        fields = []
        if data:
            for name, value in data.iteritems():
                if isinstance(value, basestring):
                    fields.append((name, value))
                else:
                    fields.extend((name + '[]', v) for v in value)
        if files:
            fields.extend(('files[%s]' % f[0], f) for f in files)

        response = self.raw_request(
            request_method, api_endpoint, (('json', '1'),),
            fields=fields, preload_content=False,
        )

        try:
            return json.load(response)
        except ValueError:
            logger.error('Invalid response returned by API endpoint %s', url)
            raise


def grouper(iterable, n):
    iterator = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(iterator, n))
        if not chunk:
            break
        yield chunk


def extract_strings(source, defaultlocale):
    logger.info('Extracting page strings (please be patient)...')
    page_strings = {}

    def record_string(page, locale, name, value, comment, fixed_strings):
        if locale != defaultlocale:
            return

        try:
            store = page_strings[page]
        except KeyError:
            store = page_strings[page] = collections.OrderedDict()

        store[name] = {'message': value}

        if fixed_strings:
            comment = comment + '\n' if comment else ''
            comment += ', '.join('{%d}: %s' % i_s
                                 for i_s in enumerate(fixed_strings, 1))
        if comment:
            store[name]['description'] = comment

    for page, format in source.list_pages():
        cms.utils.process_page(source, defaultlocale, page,
                               format=format, localized_string_callback=record_string)
    return page_strings


def configure_locales(crowdin_api, local_locales, enabled_locales,
                      defaultlocale):
    logger.info('Checking which locales are supported by Crowdin...')
    response = crowdin_api.request('GET', 'supported-languages')

    supported_locales = {l['crowdin_code'] for l in response}

    # We need to map the locale names we use to the ones that Crowdin is expecting
    # and at the same time ensure that they are supported.
    required_locales = {}
    for locale in local_locales:
        if '_' in locale:
            crowdin_locale = locale.replace('_', '-')
        elif locale in supported_locales:
            crowdin_locale = locale
        else:
            crowdin_locale = '%s-%s' % (locale, locale.upper())

        if crowdin_locale in supported_locales:
            required_locales[locale] = crowdin_locale
        else:
            logger.warning("Ignoring locale '%s', which Crowdin doesn't support",
                           locale)

    required_crowdin_locales = set(required_locales.values())
    if not required_crowdin_locales.issubset(enabled_locales):
        logger.info('Enabling the required locales for the Crowdin project...')
        crowdin_api.request(
            'POST', 'edit-project',
            data={'languages': enabled_locales | required_crowdin_locales},
        )

    return required_locales


def list_remote_files(project_info):
    def parse_file_node(node, path=''):
        if node['node_type'] == 'file':
            remote_files.add(path + node['name'])
        elif node['node_type'] == 'directory':
            dir_name = path + node['name']
            remote_directories.add(dir_name)
            for file in node.get('files', []):
                parse_file_node(file, dir_name + '/')

    remote_files = set()
    remote_directories = set()
    for node in project_info['files']:
        parse_file_node(node)
    return remote_files, remote_directories


def list_local_files(page_strings):
    local_files = set()
    local_directories = set()
    for page, strings in page_strings.iteritems():
        if strings:
            local_files.add(page + '.json')
            while '/' in page:
                page = page.rsplit('/', 1)[0]
                local_directories.add(page)
    return local_files, local_directories


def create_directories(crowdin_api, directories):
    for directory in directories:
        logger.info('Creating directory %s', directory)
        crowdin_api.request('POST', 'add-directory', data={'name': directory})


def add_update_files(crowdin_api, api_endpoint, message, files, page_strings):
    for group in grouper(files, crowdin_api.FILES_PER_REQUEST):
        files = []
        for file_name in group:
            page = os.path.splitext(file_name)[0]
            files.append((file_name, json.dumps(page_strings[page]), 'application/json'))
            del page_strings[page]
        logger.info(message, len(files))
        crowdin_api.request('POST', api_endpoint, files=files)


def upload_new_files(crowdin_api, new_files, page_strings):
    add_update_files(crowdin_api, 'add-file', 'Uploading %d new pages...',
                     new_files, page_strings)


def update_existing_files(crowdin_api, existing_files, page_strings):
    add_update_files(crowdin_api, 'update-file', 'Updating %d existing pages...',
                     existing_files, page_strings)


def upload_translations(crowdin_api, source_dir, new_files, required_locales):
    def open_locale_files(locale, files):
        for file_name in files:
            path = os.path.join(source_dir, 'locales', locale, file_name)
            if os.path.isfile(path):
                with open(path, 'rb') as f:
                    yield (file_name, f.read(), 'application/json')

    if new_files:
        for locale, crowdin_locale in required_locales.iteritems():
            for files in grouper(open_locale_files(locale, new_files),
                                 crowdin_api.FILES_PER_REQUEST):
                logger.info('Uploading %d existing translation '
                            'files for locale %s...', len(files), locale)
                crowdin_api.request('POST', 'upload-translation', files=files,
                                    data={'language': crowdin_locale})


def remove_old_files(crowdin_api, old_files):
    for file_name in old_files:
        logger.info('Removing old file %s', file_name)
        crowdin_api.request('POST', 'delete-file', data={'file': file_name})


def remove_old_directories(crowdin_api, old_directories):
    for directory in reversed(sorted(old_directories, key=len)):
        logger.info('Removing old directory %s', directory)
        crowdin_api.request('POST', 'delete-directory', data={'name': directory})


def download_translations(crowdin_api, source_dir, required_locales):
    logger.info('Requesting generation of fresh translations archive...')
    result = crowdin_api.request('GET', 'export')
    if result.get('success', {}).get('status') == 'skipped':
        logger.warning('Archive generation skipped, either '
                       'no changes or API usage excessive')

    logger.info('Downloading translations archive...')
    response = crowdin_api.raw_request('GET', 'download/all.zip')

    inverted_required_locales = {crowdin: local for local, crowdin in
                                 required_locales.iteritems()}
    logger.info('Extracting translations archive...')
    with zipfile.ZipFile(io.BytesIO(response.data), 'r') as archive:
        locale_path = os.path.join(source_dir, 'locales')
        # First clear existing translation files
        for root, dirs, files in os.walk(locale_path, topdown=True):
            if root == locale_path:
                dirs[:] = [d for d in dirs if d in required_locales]
            for f in files:
                if f.lower().endswith('.json'):
                    os.remove(os.path.join(root, f))
        # Then extract the new ones in place
        for member in archive.namelist():
            path, file_name = posixpath.split(member)
            ext = posixpath.splitext(file_name)[1]
            path_parts = path.split(posixpath.sep)
            locale, file_path = path_parts[0], path_parts[1:]
            if ext.lower() == '.json' and locale in inverted_required_locales:
                output_path = os.path.join(
                    locale_path, inverted_required_locales[locale],
                    *file_path + [file_name]
                )
                with archive.open(member) as source_file:
                    locale_file_contents = json.load(source_file)
                    if len(locale_file_contents):
                        with codecs.open(output_path, 'wb', 'utf-8') as target_file:
                            json.dump(locale_file_contents, target_file, ensure_ascii=False,
                                      sort_keys=True, indent=2, separators=(',', ': '))


def crowdin_sync(source_dir, crowdin_api_key):
    with FileSource(source_dir) as source:
        config = source.read_config()
        defaultlocale = config.get('general', 'defaultlocale')
        crowdin_project_name = config.get('general', 'crowdin-project-name')

        crowdin_api = CrowdinAPI(crowdin_api_key, crowdin_project_name)

        logger.info('Requesting project information...')
        project_info = crowdin_api.request('GET', 'info')
        page_strings = extract_strings(source, defaultlocale)

        local_locales = source.list_locales() - {defaultlocale}
        enabled_locales = {l['code'] for l in project_info['languages']}

    required_locales = configure_locales(crowdin_api, local_locales,
                                         enabled_locales, defaultlocale)

    remote_files, remote_directories = list_remote_files(project_info)
    local_files, local_directories = list_local_files(page_strings)

    # Avoid deleting all remote content if there was a problem listing local files
    if not local_files:
        logger.error('No existing strings found, maybe the project directory is '
                     'not set up correctly? Aborting!')
        sys.exit(1)

    new_files = local_files - remote_files
    new_directories = local_directories - remote_directories
    create_directories(crowdin_api, new_directories)
    upload_new_files(crowdin_api, new_files, page_strings)
    upload_translations(crowdin_api, source_dir, new_files, required_locales)

    existing_files = local_files - new_files
    update_existing_files(crowdin_api, existing_files, page_strings)

    old_files = remote_files - local_files
    old_directories = remote_directories - local_directories
    remove_old_files(crowdin_api, old_files)
    remove_old_directories(crowdin_api, old_directories)

    download_translations(crowdin_api, source_dir, required_locales)
    logger.info('Crowdin sync completed.')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print >>sys.stderr, 'Usage: python -m cms.bin.translate www_directory crowdin_project_api_key [logging_level]'
        sys.exit(1)

    logging.basicConfig()
    logger.setLevel(sys.argv[3] if len(sys.argv) > 3 else logging.INFO)

    source_dir, crowdin_api_key = sys.argv[1:3]
    crowdin_sync(source_dir, crowdin_api_key)
