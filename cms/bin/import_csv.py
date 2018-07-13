import io
import os
import sys
import argparse
import logging
import json
import csv
import itertools
import collections

import cms.utils

from cms.bin.export_csv import extract_strings
from cms.bin.export_csv import LOCALES_DIR
from cms.bin.export_csv import DELETED

logger = logging.getLogger('cms.bin.import_csv')

def main(source):
    reader = csv.DictReader(sys.stdin, dialect='excel')
    local_locales = reader.fieldnames[5:]

    # Sort input for groupby below so rows don't need to be in order
    reader_sorted = sorted(list(reader), key=lambda v: v['file'])

    # group by json file so we don't have to touch a file twice
    for page, strings in itertools.groupby(reader_sorted, lambda v: v['file']):
        # We'll iterate over strings more than once (per locale)
        strings = list(strings)

        for locale in local_locales:
            file_name = os.path.join(LOCALES_DIR, locale, page + '.json')
            try:
                with open(file_name, 'r') as file_old:
                    existing_json = json.load(
                        file_old,
                        object_pairs_hook=collections.OrderedDict)
            except IOError:
                logger.debug('File {} not found, no existing translations for {}'.format(file_name, locale))
                existing_json = {}
            except ValueError:
                logger.error('File {} exists but is not a valid JSON file.'.format(file_name))
                raise

            # NOTE: Maybe we can add warnings if the csv file contains
            # rows/translations that haven't had any effect on the json files
            changes = False
            for string in strings:
                key = string['key'].decode('utf8')
                # XXX: csv doesn't support unicode find a better way to convert
                # input to unicode for comparison/compatibility with json
                translation = string[locale].decode('utf8')

                if DELETED in string['flags']:
                    if key in existing_json:
                        changes = True
                        existing_json.pop(key)
                    continue

                if translation:
                    if key in existing_json:
                        if existing_json[key][u'message'] != translation:
                            changes = True
                            existing_json[key][u'message'] = translation
                    else:
                        changes = True
                        existing_json[key] = {u'message': translation}

            if changes:
                # XXX: not sure if this BS is neccesary but apparently it's not
                # trivial to write utf8 json files, see:
                # https://stackoverflow.com/questions/18337407/
                with io.open(file_name, 'w', encoding='utf8') as file_old:
                    file_old.write(unicode(json.dumps(
                        existing_json,
                        indent=2,
                        ensure_ascii=False,
                        encoding='utf8',
                        separators=(u',', u': '))))

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Extracts source strings from codebase')
    parser.add_argument('source', help="Path to website's repository")

    logging.basicConfig()

    logger.setLevel(logging.INFO)

    args = parser.parse_args()

    main(args.source)
