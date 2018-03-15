import os
import shutil
import pytest

from wsgi_intercept import urllib3_intercept
from wsgi_intercept import add_wsgi_intercept
from wsgi_intercept import remove_wsgi_intercept

import crowdin_mock_api
from cms.bin import translate


@pytest.fixture(scope='module')
def expect_requests():
    return [
        ('info?key=test_key&json=1', ''),
        ('supported-languages?key=test_key&json=1', ''),
        ('add-file?key=test_key&json=1', '.json'),
        ('upload-translation?key=test_key&json=1', 'simple'),
        ('delete-file?key=test_key&json=1', '.json'),
        ('delete-file?key=test_key&json=1', '.json'),
        ('delete-file?key=test_key&json=1', '.json'),
        ('delete-file?key=test_key&json=1', '.json'),
        ('delete-directory?key=test_key&json=1', ''),
        ('delete-directory?key=test_key&json=1', ''),
        ('export?key=test_key&json=1', ''),
        ('download/all.zip?key=test_key', ''),
    ]


@pytest.fixture
def api_zip(tmpdir, temp_site, request):
    input_dir = os.path.join(temp_site, 'locales')
    shutil.make_archive(tmpdir.join('all').strpath, 'zip', input_dir)
    return tmpdir.strpath


@pytest.fixture
def mock_api(temp_site, api_zip):
    app = crowdin_mock_api.load(os.path.join(temp_site, 'locales'), api_zip)
    host = 'api.crowdin.com'
    port = 443
    urllib3_intercept.install()
    add_wsgi_intercept(host, port, lambda: app.wsgi_app)
    yield app
    remove_wsgi_intercept()


def test_sync(temp_site, mock_api, expect_requests):
    translate.crowdin_sync(temp_site, 'test_key')
    for (url, data), (expect_url, expect_data) in zip(mock_api.request_log,
                                                      expect_requests):
        assert expect_url in url
        assert expect_data in data
