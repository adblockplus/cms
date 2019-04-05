import os
import sys
import argparse
import collections
import logging
import json
import csv

import cms.utils

from cms.sources import FileSource

logger = logging.getLogger('cms.bin.makejsons')

FUZZY = 'FUZZY'
NEW = 'NEW'
DELETED = 'DELETED'
LOCALES_DIR = 'locales'

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
        logger.info('Processing page {}'.format(page))
        cms.utils.process_page(source,
                               defaultlocale,
                               page,
                               format=format,
                               localized_string_callback=record_string)

    return page_strings

def update_local_files(page_strings, local_locales, default_locale):

    rows = []

    for page, strings in page_strings.items():
        # Read and parse existing default locale file if exists so we can
        # compare the strings and see what has changed
        file_name = os.path.join(LOCALES_DIR, default_locale, page + '.json')
        try:
            with open(file_name, 'r') as file_old:
                json_old = json.load(file_old, object_pairs_hook=collections.OrderedDict)
        except IOError:
            logger.info('File {} not found, no existing translations for default locale'.format(file_name))
            json_old = {}
        except ValueError:
            logger.error('File {} exists but is not a valid JSON file.'.format(file_name))
            raise

        # Open existing translations so we can include them
        existing_translations = {}
        for locale in local_locales:
            file_name = os.path.join(LOCALES_DIR, locale, page + '.json')
            try:
                with open(file_name, 'r') as file_old:
                    existing_translations[locale] = json.load(
                        file_old,
                        object_pairs_hook=collections.OrderedDict)
            except IOError:
                logger.debug('File {} not found, no existing translations for {}'.format(file_name, locale))
            except ValueError:
                logger.error('File {} exists but is not a valid JSON file.'.format(file_name))
                raise

        # Merge existing and current strings
        json_new = {}

        keys = strings.keys()
        for key in json_old.keys():
            if key not in keys:
                keys.append(key)

        for key in keys:
            row = {'file': page, 'key':key, 'flags': ''}
            value_old = json_old.get(key)
            value = value_old or {}

            if key not in strings:
                row['flags'] = DELETED
                value = json_old[key]

                # XXX: maybe we should make old description required?
                row['description'] = value.get('description', '')
                row['source_string'] = value['message']

            elif key not in json_old:
                # New string has no description
                row['description'] = ''

                row['source_string'] = strings[key]['message']

                row['flags'] = NEW
                #flags.setdefault(key, []).append(NEW)
            else:
                value = json_old[key]

                # XXX: maybe we should make old description required?
                row['description'] = value.get('description', '')

                row['source_string'] = strings[key]['message']

                if strings[key]['message'] != value['message']:
                    row['flags'] = FUZZY
                else:
                    continue


            for locale in local_locales:
                if locale in existing_translations:
                    if key in existing_translations[locale]:
                        row[locale] = existing_translations[locale][key]['message']
            rows.append(row)

    if rows:
        header = ['file', 'key', 'description', 'flags', 'source_string']
        header += list(local_locales)

        writer = csv.writer(sys.stdout, dialect='excel')

        writer.writerow(header)
        for row in rows:
            writer.writerow([row.get(key, '').encode('utf8') for key in header])

def main(source_dir):
    # XXX: add deletion of obsolete files
    with FileSource(source_dir) as source:
        config = source.read_config()
        default_locale = config.get('general', 'defaultlocale')
        page_strings = extract_strings(source, default_locale)
        local_locales = source.list_locales()

    update_local_files(page_strings, local_locales, default_locale)

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Extracts source strings from codebase')
    parser.add_argument('source', help="Path to website's repository")



    logging.basicConfig()

    logger.setLevel(logging.INFO)

    args = parser.parse_args()

    main(args.source)
