import os
import sys
import runpy

import mock
import pytest
import urllib2

from .conftest import ROOTPATH
from .utils import get_dir_contents, run_test_server
from cms.sources import FileSource


def get_expected_outputs(test_type):
    expected_out_path = os.path.join(ROOTPATH, 'tests', 'expected_output')
    outputs = get_dir_contents(expected_out_path)
    for filename in list(outputs):
        # Move test-type-specific expected outputs (e.g. "xyz@static" -> "xyz")
        # There are cases where we need to test outputs which differ depending
        # on how they are generated; either statically or dynamically
        if filename.endswith('@' + test_type):
            realname = filename.split('@')[0]
            outputs[realname] = outputs[filename]
        # Remove the expected outputs that don't apply for this test type.
        if '@' in filename:
            del outputs[filename]
    return outputs.items()


static_expected_outputs = get_expected_outputs('static')
dynamic_expected_outputs = get_expected_outputs('dynamic')


@pytest.fixture(scope='session')
def static_output(request, temp_site):
    static_out_path = os.path.join(temp_site, 'static_out')
    sys.argv = ['filler', temp_site, static_out_path]
    with mock.patch('cms.sources.FileSource.version', 1):
        runpy.run_module('cms.bin.generate_static_pages', run_name='__main__')
    return static_out_path


@pytest.fixture(scope='module')
def dynamic_server(temp_site):
    with run_test_server(temp_site) as ts:
        yield ts


@pytest.fixture(scope='session')
def output_pages(static_output):
    return get_dir_contents(static_output)


@pytest.mark.parametrize('filename,expected_output', static_expected_outputs)
def test_static(output_pages, filename, expected_output):
    if expected_output.startswith('## MISSING'):
        assert filename not in output_pages
    else:
        assert expected_output == output_pages[filename]


@pytest.mark.parametrize('filename,expected_output', dynamic_expected_outputs)
def test_dynamic(dynamic_server, filename, expected_output):
    response = urllib2.urlopen(dynamic_server + filename)
    assert expected_output == response.read().strip()


def test_cache(output_pages):
    source = FileSource(os.path.join('test_site'))
    assert source.get_cache_dir() == os.path.join('test_site', 'cache')
