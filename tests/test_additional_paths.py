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

import subprocess
import sys
import urllib2

import py
import pytest
import runpy

from cms.sources import create_source
from .utils import get_dir_contents, run_test_server


PATHS_FRAGMENT_TEMPLATE = """
[paths]
additional-paths = {}
"""


@pytest.fixture(scope='session')
def ap_site(temp_site, tmpdir_factory):
    """A website source that has another website in additional-paths."""
    base_root = py.path.local(temp_site)
    base_pages = base_root.join('pages')

    ap_root = tmpdir_factory.mktemp('ap_site')
    ap_root.join('settings.ini').write(
        base_root.join('settings.ini').read() +
        PATHS_FRAGMENT_TEMPLATE.format(base_root)
    )

    pages = ap_root.mkdir('pages')
    pages.join('filter.tmpl').write(base_pages.join('filter.tmpl').read() +
                                    'MARKER')
    pages.join('map.tmpl').write(base_pages.join('sitemap.tmpl').read())

    subprocess.check_call(['hg', 'init', ap_root.strpath])
    subprocess.check_call(['hg', '-R', ap_root.strpath,
                           'commit', '-A', '-m', 'foo'])

    return ap_root


@pytest.fixture(scope='session')
def ap_static_output(tmpdir_factory, ap_site):
    """Generate website from two source directories, return output path."""
    out_path = tmpdir_factory.mktemp('ap_out')
    saved_argv = sys.argv
    sys.argv = ['', ap_site.strpath, out_path.strpath]
    runpy.run_module('cms.bin.generate_static_pages', run_name='__main__')
    yield out_path
    sys.argv = saved_argv


def test_ap_static(ap_static_output):
    outfiles = get_dir_contents(ap_static_output.strpath)
    assert outfiles['en/filter'].endswith('MARKER')  # We can override pages.
    assert 'sitemap' in outfiles['en/map']           # The lists of pages are
    assert 'map' in outfiles['en/sitemap']           # merged.


@pytest.fixture(scope='module')
def dynamic_server(ap_site):
    with run_test_server(ap_site.strpath) as ts:
        yield ts


def test_dynamic(dynamic_server):
    response = urllib2.urlopen(dynamic_server + 'en/filter')
    assert response.read().endswith('MARKER')


def test_create_source(tmpdir):
    """Create a hierarchy of multi-sources testing different config options."""
    one = tmpdir.mkdir('one')
    two = tmpdir.mkdir('two')
    three = tmpdir.mkdir('three')
    four = two.mkdir('four')

    one_ap = '\n    {}\n    {}'.format(two.strpath, '../three')
    one.join('settings.ini').write(PATHS_FRAGMENT_TEMPLATE.format(one_ap))
    one.join('one').write('')

    two.join('settings.ini').write(PATHS_FRAGMENT_TEMPLATE.format('four'))
    two.join('two').write('')

    three.join('three').write('')
    three.join('settings.ini').write('')

    four.join('four').write('')
    four.join('settings.ini').write('[paths]')

    source = create_source(one.strpath)

    for name in ['one', 'two', 'three', 'four']:
        assert source.has_file(name)
