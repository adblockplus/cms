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

from __future__ import unicode_literals

import json
import os

import pytest

from cms.translations.xtm import utils
import cms.translations.xtm.constants as const
from cms.sources import FileSource
from cms.translations.xtm.xtm_api import XTMCloudAPI
from tests.utils import exception_test, XtmMockArgs

_API_TOKEN_VALID = 'TheXTM-APIToken-VALID'
_PROJECT_ID = 1234


@pytest.fixture
def toydir(tmpdir):
    """Toy directory fixture with two locales - 'de' and 'en'."""
    toydir = tmpdir.mkdir('toydir')

    en_dir = toydir.mkdir('en')
    en_dir.join('file.json').write(json.dumps({'a': 'b'}))

    de_dir = toydir.mkdir('de')
    de_dir.join('file.json').write(json.dumps({'a': 'b'}))
    de_dir.join('file.txt').write('test')

    return toydir


def test_get_files_to_upload(temp_site):
    """Generation of correct datatype for the XTMCloudAPI class."""
    files = utils.get_files_to_upload(FileSource(temp_site))

    assert 'translate.json' in files
    assert 'translate-not-enough.json' in files


def test_read_token_invalid():
    """Test if appropriate exception is raised when no token is found."""
    exp_msg = const.ErrorMessages.NO_TOKEN_PROVIDED.format(
        const.Token.CREATION_CMD,
    )
    with pytest.raises(Exception) as err:
        utils.read_token()
    assert exp_msg in str(err.value)


def test_read_token_valid():
    """Test if the token is read correctly when the env is setup."""
    env_var = const.Token.ENV_VAR
    token = 'test_token'
    os.environ[env_var] = token

    try:
        assert token == utils.read_token()
    finally:
        del os.environ[env_var]


def test_sanitize_project_name_characters():
    """Test if invalid name characters are replaced as expected."""
    test_in = '{0}{1}{0}'.format(
        'test', ''.join(const.ProjectName.INVALID_CHARS),
    )
    exp_out = '{0}{1}{0}'.format(
        'test',
        const.ProjectName.NAME_WILDCARD * len(const.ProjectName.INVALID_CHARS),
    )

    assert exp_out == utils.sanitize_project_name(test_in)


def test_sanitize_project_name_length():
    """Test if names that are too long are truncated as expected."""
    test_in = 'a' * (const.ProjectName.MAX_LENGTH + 10)
    exp_out = 'a' * const.ProjectName.MAX_LENGTH

    assert exp_out == utils.sanitize_project_name(test_in)


def test_map_locales(temp_site):
    """Test if a local website's languages are mapped to XTM's format."""
    test_source = FileSource(str(temp_site))
    exp_out = {'de_DE'}

    assert exp_out == utils.map_locales(test_source)


def test_remote_to_local_good(temp_site):
    """Test if a remote filename is resolved to a valid OS path."""
    test_in = '___foo___bar___faz___test.json'
    exp_out = os.path.join(str(temp_site), 'foo', 'bar', 'faz', 'test.json')

    assert exp_out == utils.remote_to_local(test_in, str(temp_site),
                                            locales=['foo'])


def test_remote_to_local_exception(temp_site):
    test_in = '___foo___bar___faz___test.json'
    exp_msg = const.ErrorMessages.CANT_RESOLVE_REMOTE_LANG.format('foo')

    exception_test(utils.remote_to_local, Exception, exp_msg, test_in,
                   str(temp_site), locales=['bar'])


def test_run_and_wait_no_err():
    exp_out = 'test'

    def func():
        return exp_out

    assert exp_out == utils.run_and_wait(func, Exception, '')


def test_run_and_wait_with_params():
    test_in = 'test'

    def func(a):
        return a

    assert test_in == utils.run_and_wait(func, Exception, '', a=test_in)


@pytest.mark.slow_test
def test_run_and_wait_infinite():
    exp_msg = 'ERROR'

    def func():
        raise Exception(exp_msg)

    with pytest.raises(Exception) as err:
        utils.run_and_wait(func, Exception, exp_msg, retries=1)

    assert exp_msg == str(err.value)


def test_resolve_locales(intercept_populated, temp_site):
    """Test if locales are resolved correctly.

    In this environment, no languages have to be added.
    """
    api = XTMCloudAPI(_API_TOKEN_VALID)
    source = FileSource(str(temp_site))
    source.write_to_config('XTM', 'project_id', str(_PROJECT_ID))

    utils.resolve_locales(api, source)


def test_resolve_locales_adds_langs(intercept, temp_site):
    """Test if locales are resolved correctly.

    In this environment, new target languages are added.
    """
    api = XTMCloudAPI(_API_TOKEN_VALID)
    source = FileSource(str(temp_site))
    source.write_to_config('XTM', 'project_id', str(_PROJECT_ID))
    exp_targets = {'de_DE'}

    utils.resolve_locales(api, source)

    assert exp_targets == api.get_target_languages(_PROJECT_ID)


def test_resolve_locales_raise_exception(intercept_populated, temp_site):
    """Test if locales are resolved correctly.

    In this environment, the API has more target languages configured than are
    available online. We except an exception to be raised.
    """
    api = XTMCloudAPI(_API_TOKEN_VALID)
    api.add_target_languages(_PROJECT_ID, ['ro_RO'])
    source = FileSource(str(temp_site))
    source.write_to_config('XTM', 'project_id', str(_PROJECT_ID))
    exp_msg = ('The following languages are enabled in the API, but not '
               "listed in locales: set(['ro_RO'])! Please remove them manually"
               ' from project number 1234 and then re-run the script!')

    exception_test(utils.resolve_locales, Exception, exp_msg, api, source)


def test_list_locales(toydir):
    """Test if the the locales are listed correctly."""
    assert utils.get_locales(str(toydir), 'en') == ['de']


def test_clear_files(toydir):
    """Test if local translation files are deleted, as expected."""
    required_locales = ['de']

    utils.clear_files(str(toydir), required_locales)

    assert os.path.exists(str(toydir.join('en/file.json')))
    assert os.path.isfile(str(toydir.join('de/file.txt')))
    assert not os.path.exists(str(toydir.join('de/file.json')))


@pytest.mark.parametrize('path', ['de/test.json', 'de/dir1/dir2/test.json'])
def test_write_data(toydir, path):
    """Test if writing data to files works as expected."""
    data = bytes(json.dumps({'a': 'b'}))

    utils.write_to_file(data, str(toydir.join(path)))

    assert toydir.join(path).read('rb') == data


@pytest.mark.parametrize('id_in,name,exp_err,exp_msg,exp_id', [
    (1234, 'foo', Exception,
     const.ErrorMessages.WORKFLOW_NAME_AND_ID_PROVIDED, None),
    (None, None, Exception, const.ErrorMessages.NO_WORKFLOW_INFO, None),
    (None, 'foo', Exception,
     const.ErrorMessages.NO_WORKFLOW_FOR_NAME.format('foo'), None),
    (1234, None, None, None, 1234),
    (None, 'workflow1', None, None, 2222),
])
def test_handle_workflows(intercept, id_in, name, exp_err, exp_msg, exp_id):
    """"""
    namespace = XtmMockArgs.CreationArgsNamespace()
    namespace.workflow_id = id_in
    namespace.workflow_name = name

    api = XTMCloudAPI(_API_TOKEN_VALID)

    if exp_err:
        exception_test(utils.extract_workflow_id, exp_err, exp_msg, api,
                       namespace)
    else:
        id_out = utils.extract_workflow_id(api, namespace)

        assert id_out == exp_id


def test_extract_unicode_strings(temp_site):
    """Test correct extraction of unicode strings for translation."""
    with FileSource(temp_site) as fs:
        strings = utils.extract_strings(fs)

    assert '\u0376' in strings['translate-unicode']['simple']['message']
