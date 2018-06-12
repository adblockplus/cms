import os
import pytest
import shutil


ROOTPATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope='session')
def temp_site(tmpdir_factory):
    out_dir = tmpdir_factory.mktemp('temp_out')
    site_dir = out_dir.join('test_site').strpath

    shutil.copytree(os.path.join(ROOTPATH, 'tests', 'test_site'), site_dir)
    yield site_dir
