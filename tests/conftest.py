import os
import pytest
import shutil
import subprocess


ROOTPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope='session')
def temp_site(tmpdir_factory):
    out_dir = tmpdir_factory.mktemp('temp_out')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    subprocess.check_call(['hg', 'init', site_dir])
    subprocess.check_call(['hg', '-R', site_dir, 'commit', '-A', '-m', 'foo'])

    subprocess.check_call(['hg', '-R', site_dir, 'bookmark', 'master'])
    subprocess.check_call(['hg', '-R', site_dir, 'bookmark', 'test'])
    subprocess.check_call(['touch', os.path.join(site_dir, 'pages', 'bar.md')])
    subprocess.check_call(['hg', '-R', site_dir, 'commit', '-A', '-m', 'bar'])
    yield site_dir
