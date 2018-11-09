import os
import sys
import runpy

import mock
import pytest

from .conftest import ROOTPATH
from .utils import get_dir_contents, exception_test
from cms.sources import FileSource
from cms.bin.test_server import DynamicServerHandler


def get_expected_outputs(test_type, with_common=True):
    root = os.path.join(ROOTPATH, 'tests', 'expected_output')
    outputs = {}
    if with_common:
        outputs = get_dir_contents(os.path.join(root, 'common'))
    outputs.update(get_dir_contents(os.path.join(root, test_type)))
    return outputs.items()


static_expected_outputs = get_expected_outputs('static')
dynamic_expected_outputs = get_expected_outputs('dynamic')
relative_expected_outputs = get_expected_outputs('relative', False)


def generate_static_pages(temp_site, tmpdir_factory, *extra_args):
    dst_path = str(tmpdir_factory.mktemp('static'))
    sys.argv = ['filler', temp_site, dst_path] + list(extra_args)
    with mock.patch('cms.sources.FileSource.version', 1):
        runpy.run_module('cms.bin.generate_static_pages',
                         run_name='__main__')
    return get_dir_contents(dst_path)


@pytest.fixture(scope='session')
def output_pages(temp_site, tmpdir_factory):
    return generate_static_pages(temp_site, tmpdir_factory)


@pytest.fixture(scope='session')
def output_pages_relative(temp_site, tmpdir_factory):
    return generate_static_pages(temp_site, tmpdir_factory, '--relative')


@pytest.mark.parametrize('filename,expected_output', static_expected_outputs)
def test_static(output_pages, filename, expected_output):
    if expected_output.startswith('## MISSING'):
        assert filename not in output_pages
    else:
        assert expected_output == output_pages[filename]


@pytest.mark.parametrize('filename,expected_output', relative_expected_outputs)
def test_static_relative(output_pages_relative, filename, expected_output):
    if expected_output.startswith('## MISSING'):
        assert filename not in output_pages_relative
    else:
        assert expected_output == output_pages_relative[filename]


def test_cache(output_pages):
    source = FileSource(os.path.join('test_site'))
    assert source.get_cache_dir() == os.path.join('test_site', 'cache')


@pytest.mark.parametrize('filename,expected_output', dynamic_expected_outputs)
def test_dynamic_server_handler(filename, expected_output, temp_site):

    def cleanup(page):
        return page.replace(os.linesep, '').strip()

    handler = DynamicServerHandler('localhost', 5000, str(temp_site))
    environ = {'PATH_INFO': filename}

    generated_page = handler(environ, lambda x, y: None)

    assert cleanup(expected_output) == cleanup(generated_page[0])


@pytest.mark.parametrize('page', ['en/translate', '/en/translate'])
def test_dynamic_server_handler_with_conflicts(page, temp_site_with_conflicts):
    handler = DynamicServerHandler('localhost', 5000,
                                   str(temp_site_with_conflicts))
    environ = {'PATH_INFO': page}
    exp_msg = 'The requested page conflicts with another page.'

    exception_test(handler, Exception, exp_msg, environ, lambda x, y: None)
