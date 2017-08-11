import os
import sys
import time
import runpy
import signal
import pytest
import urllib2
import subprocess
from conftest import ROOTPATH


def get_dir_contents(path):
    dirdata = {}
    for dirpath, dirnames, filenames in os.walk(path):
        for output_file in filenames:
            filepath = os.path.join(dirpath, output_file)
            with open(filepath) as f:
                locale = os.path.split(os.path.split(filepath)[0])[1]
                dirdata[os.path.join(locale, output_file)] = f.read().strip()
    return dirdata


def get_expected_outputs(test_type):
    expected_out_path = os.path.join(ROOTPATH, 'tests', 'expected_output')
    outputs = get_dir_contents(expected_out_path)
    for filename in list(outputs):
        # Move test-type-specific expected outputs (e.g. "xyz@static" -> "xyz")
        # and remove the expected outputs that don't apply for this test type.
        if filename.endswith('@' + test_type):
            realname = filename.split('@')[0]
            outputs[realname] = outputs[filename]
        if '@' in filename:
            del outputs[filename]
    return outputs.items()


static_expected_outputs = get_expected_outputs('static')
dynamic_expected_outputs = get_expected_outputs('dynamic')


@pytest.fixture(scope='session', params=['master', None])
def revision(request):
    return request.param


@pytest.fixture(scope='session')
def static_output(revision, request, temp_site):
    static_out_path = os.path.join(temp_site, 'static_out')
    sys.argv = ['filler', temp_site, static_out_path]
    if revision is not None:
        sys.argv += ['--rev', revision]

    runpy.run_module('cms.bin.generate_static_pages', run_name='__main__')
    return static_out_path


@pytest.yield_fixture()
def dynamic_server(temp_site):
    args = ['python', 'runserver.py', temp_site]
    # Werkzeug is a dependency of flask which we are using for the mock api
    # however there is an issue with Werkzeug that prevents it from properly
    # handling the SIGTERM sent by p.kill() or terminate()
    # Issue: https://github.com/pallets/werkzeug/issues/58
    p = subprocess.Popen(args, stdout=subprocess.PIPE, preexec_fn=os.setsid)
    time.sleep(0.5)
    yield 'http://localhost:5000/'
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)


@pytest.fixture(scope='session')
def output_pages(static_output):
    return get_dir_contents(static_output)


@pytest.mark.parametrize('filename,expected_output', static_expected_outputs)
def test_static(output_pages, filename, expected_output):
    assert output_pages[filename] == expected_output


@pytest.mark.parametrize('filename,expected_output', dynamic_expected_outputs)
def test_dynamic(dynamic_server, filename, expected_output):
    response = urllib2.urlopen(dynamic_server + filename)
    assert response.read().strip() == expected_output


def test_revision_arg(revision, output_pages):
    if revision is None:
        assert 'en/bar' in output_pages
    else:
        assert 'en/bar' not in output_pages
