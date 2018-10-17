# This file is part of the Adblock Plus web scripts,
# Copyright (C) 2006-present eyeo GmbH
#
# Adblock Plus is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# Adblock Plus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adblock Plus.  If not, see <http://www.gnu.org/licenses/>.

import os

import pytest

from cms.bin.generate_static_pages import generate_pages


@pytest.fixture
def target_dir_with_file(tmpdir):
    target_dir = tmpdir.mkdir('out_file').strpath
    os.mkdir(os.path.join(target_dir, 'en'))

    with open(os.path.join(target_dir, 'en', 'foo'), 'w') as f:
        f.write('test\n')

    yield target_dir


@pytest.fixture
def target_dir_with_dir(tmpdir):
    target_dir = tmpdir.mkdir('out_dir').strpath
    os.makedirs(os.path.join(target_dir, 'en', 'translate'))

    yield target_dir


@pytest.fixture
def target_dir_with_fifo(tmpdir):
    target_dir = tmpdir.mkdir('out_dir').strpath
    os.mkdir(os.path.join(target_dir, 'en'))
    os.mkfifo(os.path.join(target_dir, 'en', 'translate'))

    yield target_dir


def test_generate_dir_instead_of_file(temp_site, target_dir_with_file):
    """Case where a file from previous version becomes a directory."""
    generate_pages(str(temp_site), str(target_dir_with_file))

    assert os.path.isdir(os.path.join(target_dir_with_file, 'en', 'foo'))


def test_generate_file_instead_of_dir(temp_site, target_dir_with_dir):
    """Case where a directory from previous version becomes a file."""
    generate_pages(str(temp_site), str(target_dir_with_dir))

    assert os.path.isfile(os.path.join(target_dir_with_dir, 'en', 'translate'))


def test_generate_fifo_instead_of_file(temp_site, target_dir_with_fifo,
                                       script_runner):
    """Case with an unsupported item encountered (FIFO)."""
    with pytest.raises(Exception) as exp:
        generate_pages(str(temp_site), str(target_dir_with_fifo))

    assert 'It is neither a file, nor a directory!' in str(exp.value)
