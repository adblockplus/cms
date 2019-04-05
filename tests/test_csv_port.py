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
import StringIO
import sys

import runpy


def test_csv_export(temp_site, mocker):
    # We must be in the directory of the website, otherwise the CSV export
    # script doesn't work (this probably needs fixing).
    old_cwd = os.getcwd()
    os.chdir(temp_site)                    

    try:
        stdout_mock = mocker.patch('sys.stdout', StringIO.StringIO())
        mocker.patch('sys.argv', ['', temp_site])
        runpy.run_module('cms.bin.export_csv', run_name='__main__')

        # Take all the lines related to `translate.md` page.
        csv_lines = [
            line.split(',') for line in stdout_mock.getvalue().split('\n')
            if line.startswith('translate,')
        ]

        # Check that the strings are in the same order as they are in the page,
        # followed by deleted strings in the order of the JSON file.
        # 'simple' is skipped by the export script because it's the same in the
        # translation file and in the page (I assume this is correct).
        order = [l[1] for l in csv_lines]
        assert order == ['fix-ts', 'nested-ts', 'nested-link', 'nested-link2',
                         'linked-ts', 'linked-ts2', 'entity-ts', 'entity-lnk',
                         'deleted', 'also-deleted']

        # Check flags for special strings.
        values = {l[1]: l[2:] for l in csv_lines}
        assert values['fix-ts'][1] == 'FUZZY'
        assert values['deleted'][1] == 'DELETED'
    finally:
        os.chdir(old_cwd)
