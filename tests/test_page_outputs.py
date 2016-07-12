import os
import sys
import shutil
import time
import runpy
import pytest
import urllib2
import subprocess

ROOTPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_dir_contents(path):
    return_data = {}
    for dirpath, dirnames, filenames in os.walk(path):
        for output_file in filenames:
            with open(os.path.join(dirpath, output_file)) as f:
                return_data[output_file] = f.read()
    return return_data


def get_expected_outputs():
    expected_out_path = os.path.join(ROOTPATH, 'tests', 'expected_output')
    return get_dir_contents(expected_out_path).items()

expected_outputs = get_expected_outputs()


@pytest.fixture(scope='session')
def temp_site(tmpdir_factory):
    out_dir = tmpdir_factory.mktemp('temp_out')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    subprocess.check_call(['hg', 'init', site_dir])
    subprocess.check_call(['hg', '-R', site_dir, 'commit', '-A', '-m', 'foo'])
    return site_dir


@pytest.fixture(scope='session')
def static_output(request, temp_site):
    static_out_path = os.path.join(temp_site, 'static_out')
    sys.argv = ['filler', temp_site, static_out_path]
    runpy.run_module('cms.bin.generate_static_pages', run_name='__main__')
    return static_out_path


@pytest.yield_fixture(scope='session')
def dynamic_server(temp_site):
    p = subprocess.Popen(['python', 'runserver.py', temp_site])
    time.sleep(0.5)
    yield 'http://localhost:5000/root/'
    p.terminate()


@pytest.fixture(scope='session')
def output_pages(static_output):
    return get_dir_contents(static_output)


@pytest.mark.parametrize('filename,expected_output', expected_outputs)
def test_static(output_pages, filename, expected_output):
    assert output_pages[filename] == expected_output


@pytest.mark.parametrize('filename,expected_output', expected_outputs)
def test_dynamic(dynamic_server, filename, expected_output):
    response = urllib2.urlopen(dynamic_server + filename)
    assert response.read() == expected_output
