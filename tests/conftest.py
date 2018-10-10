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
