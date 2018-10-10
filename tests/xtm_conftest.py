from __future__ import unicode_literals

import os
import shutil
import json

import pytest
from cms.sources import FileSource
from wsgi_intercept import add_wsgi_intercept
from wsgi_intercept import remove_wsgi_intercept
from wsgi_intercept import requests_intercept

from tests.xtm_mock_api import get_configured_app

_INTERCEPT_PORT = 443
_INTERCEPT_HOST = 'wstest2.xtm-intl.com'

ROOTPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def temp_site_invalid_locales(tmpdir):
    out_dir = tmpdir.mkdir('temp_out_invalid_locales')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    invalid_locale = site_dir.join('locales').mkdir('foo')
    invalid_locale.join('test.json').write(json.dumps({'a': 'b'}))
    return site_dir


@pytest.fixture
def temp_site_invalid_project(tmpdir):
    out_dir = tmpdir.mkdir('temp_out_invalid')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    with FileSource(str(site_dir)) as fs:
        fs.write_to_config('XTM', 'project_id', '1111')

    return site_dir


@pytest.fixture
def temp_site_valid_project(tmpdir):
    out_dir = tmpdir.mkdir('temp_out_valid')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    with FileSource(str(site_dir)) as fs:
        fs.write_to_config('XTM', 'project_id', '1234')

    return site_dir


@pytest.fixture
def temp_site_no_target_files(tmpdir):
    out_dir = tmpdir.mkdir('temp_out_no_targets')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    with FileSource(str(site_dir)) as fs:
        fs.write_to_config('XTM', 'project_id', '9999')

    return site_dir


@pytest.fixture
def temp_site_function_scope(tmpdir):
    out_dir = tmpdir.mkdir('temp_site_func')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)

    return site_dir


@pytest.fixture
def intercept():
    app = get_configured_app()
    requests_intercept.install()
    add_wsgi_intercept(_INTERCEPT_HOST, _INTERCEPT_PORT, lambda: app)
    yield app
    remove_wsgi_intercept()


@pytest.fixture
def intercept_populated():
    files = [
        {
            'name': 'file.json',
            'data': json.dumps({'foo': 'bar', 'faz': 'baz'}),
        },
        {
            'name': '___foo___file-utf8.json',
            'data': json.dumps({'foo': '\u1234'}),
        },
    ]
    targets = ['de_DE']
    app = get_configured_app(files=files, target_langs=targets)
    requests_intercept.install()
    add_wsgi_intercept(_INTERCEPT_HOST, _INTERCEPT_PORT, lambda: app)
    yield app
    remove_wsgi_intercept()


@pytest.fixture
def intercept_too_many_targets():
    targets = ['de_DE', 'es_ES']
    app = get_configured_app(target_langs=targets)
    requests_intercept.install()
    add_wsgi_intercept(_INTERCEPT_HOST, _INTERCEPT_PORT, lambda: app)
    yield app
    remove_wsgi_intercept()
