from __future__ import unicode_literals

import os
import pytest
import shutil

pytest_plugins = [
    'tests.xtm_conftest',
]

_INTERCEPT_PORT = 443
_INTERCEPT_HOST = 'wstest2.xtm-intl.com'

ROOTPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope='session')
def temp_site(tmpdir_factory):
    out_dir = tmpdir_factory.mktemp('temp_out')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    yield site_dir


@pytest.fixture(scope='session')
def temp_site_with_conflicts(tmpdir_factory):
    out_dir = tmpdir_factory.mktemp('temp_out_conflicts')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    translate_file = os.path.join(site_dir, 'locales', 'en', 'translate')
    with open(translate_file, 'w') as f:
        f.write('Page with conflicts')

    yield site_dir
