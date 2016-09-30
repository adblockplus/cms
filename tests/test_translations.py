import os
import shutil
import pytest
from wsgi_intercept import urllib3_intercept
from wsgi_intercept import add_wsgi_intercept
from wsgi_intercept import remove_wsgi_intercept

from crowdin_mock_api import app
from cms.bin import translate


@pytest.fixture(scope='module')
def expect_requests():
    return [
        ('info?key=test_key&json=1', ''),
        ('supported-languages?key=test_key&json=1', ''),
        ('add-file?key=test_key&json=1', 'translate.json'),
        ('upload-translation?key=test_key&json=1', 'test_sample'),
        ('delete-file?key=test_key&json=1', 'translate.json'),
        ('delete-file?key=test_key&json=1', 'translate.json'),
        ('delete-directory?key=test_key&json=1', 'de'),
        ('delete-directory?key=test_key&json=1', 'en'),
        ('export?key=test_key&json=1', ''),
        ('download/all.zip?key=test_key', ''),
    ]


@pytest.fixture(scope='module')
def make_crowdin_zip(temp_site):
    zip_name = os.path.join('tests', 'all')
    input_dir = os.path.join(temp_site, 'locales')
    shutil.make_archive(zip_name, 'zip', input_dir)
    yield None
    os.remove(zip_name + '.zip')


@pytest.fixture()
def make_intercept(scope='module'):
    host = 'api.crowdin.com'
    port = 443
    urllib3_intercept.install()
    add_wsgi_intercept(host, port, lambda: app.wsgi_app)
    yield None
    remove_wsgi_intercept()


def test_sync(temp_site, make_intercept, make_crowdin_zip, expect_requests):
    translate.crowdin_sync(temp_site, 'test_key')
    for (url, data), (expect_url, expect_data) in zip(
                                                      app.request_log,
                                                      expect_requests):
        assert expect_url in url
        assert expect_data in data
