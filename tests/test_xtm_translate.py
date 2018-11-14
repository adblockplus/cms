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

import os
from ConfigParser import SafeConfigParser
import io
import sys
import json

import pytest

from cms.translations.xtm import constants as const
from cms.translations.xtm.cli import (
    generate_token, handle_projects as main_project_handler,
)
from tests.utils import XtmMockArgs

_CMD_START = ['python', '-m', 'cms.bin.xtm_translations']

_ENV_NO_TOKEN = dict(os.environ)
_ENV_NO_TOKEN.pop(const.Token.ENV_VAR, None)

_ENV_TOKEN_VALID = dict(os.environ)
_ENV_TOKEN_VALID[const.Token.ENV_VAR] = 'TheXTM-APIToken-VALID'

_ENV_TOKEN_INVALID = dict(os.environ)
_ENV_TOKEN_INVALID[const.Token.ENV_VAR] = 'TheXTM-APIToken-INVALID'

_CREATION_ARGS_DEFAULT = ['--name', 'bar', '--desc', 'foo', '--client-id',
                          '10', '--ref-id', 'faz', '--workflow-id', '20']
_CREATION_ARGS_INVALID_TYPE_1 = ['--name', 'bar', '--desc', 'foo',
                                 '--client-id', 'foo', '--ref-id', 'faz',
                                 '--workflow-id', '3']
_CREATION_ARGS_INVALID_TYPE_2 = ['--name', 'bar', '--desc', 'foo',
                                 '--client-id', '23', '--ref-id', 'faz',
                                 '--workflow-id', 'foo']

_UploadArgsNamespace = XtmMockArgs.UploadArgsNamespace
_CreationArgsNamespace = XtmMockArgs.CreationArgsNamespace
_DownloadArgsNamespace = XtmMockArgs.DownloadArgsNamespace


@pytest.fixture
def env_valid_token():
    old_env = os.environ
    os.environ = _ENV_TOKEN_VALID
    yield True
    os.environ = old_env


@pytest.mark.script_launch_mode('subprocess')
@pytest.mark.parametrize('args,exp_msg', [
    (['-h'], 'usage: xtm_translations.py [-h] [-v] '
             '{login,create,upload,download} ...'),
    (['create', '-h'], 'usage: xtm_translations.py create [-h] --name NAME '
                       '--desc DESC --client-id CLIENT_ID --ref-id REF_ID '
                       '[--workflow-id WORKFLOW_ID] [--source-lang '
                       'SOURCE_LANG] [--save-id] [--workflow-name '
                       'WORKFLOW_NAME] [source_dir]'),
    (['upload', '-h'], 'usage: xtm_translations.py upload [-h] '
                       '[--no-overwrite] [source_dir]'),
    (['download', '-h'], 'usage: xtm_translations.py download [-h] '
                         '[source_dir]'),
])
def test_usage_messages(args, exp_msg, script_runner):
    """Test if appropriate usage messages are displayed."""
    cmd = list(_CMD_START)
    cmd.extend(args)
    ret = script_runner.run(*cmd)

    usg_msg = ret.stdout.replace('\n', '').replace(' ', '')

    assert exp_msg.replace(' ', '') in usg_msg


@pytest.mark.script_launch_mode('subprocess')
@pytest.mark.parametrize('args', [
    ['create', '--name', 'bar', '--desc', 'foo', '--client-id', '1',
     '--ref-id', 'faz', '--workflow-id', '3'],
    ['upload'],
    ['download'],
])
def test_default_source_directory(args, script_runner):
    """Test if the source directory if set to default if not provided."""
    exp = const.ErrorMessages.NO_TOKEN_PROVIDED.split('\n')[0]
    cmd = list(_CMD_START)
    cmd.extend(args)

    ret = script_runner.run(*cmd)

    assert not ret.success
    assert exp in ret.stderr


@pytest.mark.script_launch_mode('subprocess')
@pytest.mark.parametrize('source_dir,args,env,exp_msg', [
    ('str(temp_site)', _CREATION_ARGS_INVALID_TYPE_1, _ENV_NO_TOKEN,
     "--client-id: invalid int value: 'foo'"),
    ('str(temp_site)', _CREATION_ARGS_INVALID_TYPE_2, _ENV_NO_TOKEN,
     "--workflow-id: invalid int value: 'foo'"),
    ('str(temp_site)', _CREATION_ARGS_DEFAULT, _ENV_NO_TOKEN,
     const.ErrorMessages.NO_TOKEN_PROVIDED.split('\n')[0]),
    ('str(temp_site_valid_project)', _CREATION_ARGS_DEFAULT, _ENV_TOKEN_VALID,
     const.ErrorMessages.PROJECT_EXISTS.format(1234)),
    ('str(temp_site)', _CREATION_ARGS_DEFAULT, _ENV_TOKEN_INVALID,
     'Authentication failed'),
])
def test_creation_error_messages(temp_site, intercept, script_runner, args,
                                 source_dir, temp_site_valid_project, env,
                                 exp_msg):
    """Test if error cases are treated correctly when creating a project."""
    cmd = list(_CMD_START)
    cmd.extend(['create', eval(source_dir)])
    cmd.extend(args)

    ret = script_runner.run(*cmd, env=env)

    assert not ret.success
    assert exp_msg in ret.stderr


def test_creation_correct(temp_site, intercept, env_valid_token):
    """Test if a project is created correctly, given the appropriate args."""
    namespace = _CreationArgsNamespace()
    namespace.source_dir = str(temp_site)
    main_project_handler(namespace)


def test_creation_save_id(temp_site, intercept, env_valid_token):
    """Test the project id is saved after successfully creating a project."""
    namespace = _CreationArgsNamespace()
    namespace.source_dir = str(temp_site)
    namespace.save_id = True
    main_project_handler(namespace)
    cnf = SafeConfigParser()
    try:
        with io.open(os.path.join(temp_site, 'settings.ini'),
                     encoding='utf-8') as f:
            cnf_data = f.read()
            cnf.readfp(io.StringIO(cnf_data))
            project_id = cnf.get(const.Config.XTM_SECTION,
                                 const.Config.PROJECT_OPTION)

            assert int(project_id) == 1234
    finally:
        cnf.remove_option(const.Config.XTM_SECTION,
                          const.Config.PROJECT_OPTION)
        cnf.write(open(os.path.join(temp_site, 'settings.ini'), 'w'))


def test_login(intercept, monkeypatch, capsys):
    """Test if the login functionality works as expected."""
    exp_output = const.Token.SAVE_COMMAND.format(const.Token.ENV_VAR,
                                                 'TheXTM-APIToken-VALID')
    monkeypatch.setattr(
        'cms.translations.xtm.cli.input_fn',
        lambda inp: 'admin' if 'username' in inp.lower() else '20',
    )
    monkeypatch.setattr('getpass.getpass', lambda prompt: 'pass')

    generate_token(None)
    out, err = capsys.readouterr()

    assert err == ''
    assert exp_output in out


def test_login_wrong_credentials(intercept, monkeypatch, capsys):
    """Test exception handling when generating the tokens."""
    monkeypatch.setattr(
        'cms.translations.xtm.cli.input_fn',
        lambda inp: 'foo' if 'username' in inp.lower() else '50',
    )
    monkeypatch.setattr('getpass.getpass', lambda prompt: 'pass')
    monkeypatch.setattr('sys.exit', lambda x: sys.stderr.write(str(x)))

    generate_token(None)
    out, err = capsys.readouterr()

    assert 'Invalid credentials' in err
    assert out == ''


@pytest.mark.script_launch_mode('subprocess')
@pytest.mark.parametrize('args,env,exp_msg', [
    (['str(temp_site)'], _ENV_NO_TOKEN,
     const.ErrorMessages.NO_TOKEN_PROVIDED.split('\n')[0]),
    (['str(temp_site)'], _ENV_TOKEN_VALID, 'No project configured'),
])
def test_upload_error_messages_as_script(temp_site, script_runner, args, env,
                                         exp_msg):
    cmd = list(_CMD_START)
    cmd.append('upload')

    cmd.extend(list(map(eval, args)))

    ret = script_runner.run(*cmd, env=env)

    assert not ret.success
    assert exp_msg in ret.stderr


def test_upload_too_many_languages(intercept_too_many_targets,
                                   env_valid_token, temp_site_valid_project):
    namespace = _UploadArgsNamespace()
    namespace.source_dir = str(temp_site_valid_project)

    with pytest.raises(Exception) as err:
        main_project_handler(namespace)

    assert 'languages are enabled in the API, but not listed in locales' in \
           str(err.value)


def test_upload_successful(intercept, env_valid_token,
                           temp_site_valid_project, monkeypatch, capsys):
    namespace = _UploadArgsNamespace()
    namespace.source_dir = str(temp_site_valid_project)
    monkeypatch.setattr('logging.info', lambda x: sys.stderr.write(x))

    main_project_handler(namespace)
    _, err = capsys.readouterr()

    assert const.InfoMessages.FILES_UPLOADED in err
    assert 'Created job 1' in err


@pytest.mark.script_launch_mode('subprocess')
@pytest.mark.parametrize('env,exp_msg', [
    (_ENV_NO_TOKEN, const.ErrorMessages.NO_TOKEN_PROVIDED.split('\n')[0]),
    (_ENV_TOKEN_VALID, 'No project configured'),
])
def test_download_error_messages_as_script(temp_site, script_runner, env,
                                           exp_msg):
    cmd = list(_CMD_START)
    cmd.extend(['download', str(temp_site)])

    ret = script_runner.run(*cmd, env=env)

    assert not ret.success
    assert exp_msg in ret.stderr


def test_download_no_target_files(temp_site_no_target_files, env_valid_token,
                                  intercept, monkeypatch, capsys):
    namespace = _DownloadArgsNamespace()
    namespace.source_dir = str(temp_site_no_target_files)
    monkeypatch.setattr('sys.exit', lambda x: sys.stderr.write(x))

    main_project_handler(namespace)
    out, err = capsys.readouterr()

    assert const.ErrorMessages.NO_TARGET_FILES_FOUND in err


def test_download_saves_to_disk(temp_site_valid_project, env_valid_token,
                                intercept_populated):
    namespace = _DownloadArgsNamespace()
    namespace.source_dir = str(temp_site_valid_project)

    main_project_handler(namespace)

    with open(os.path.join(temp_site_valid_project, 'locales', 'de',
                           'file.json')) as f:
        assert json.dumps({'foo': 'bar', 'faz': 'baz'}) == f.read()

    with open(os.path.join(temp_site_valid_project, 'locales', 'de', 'foo',
                           'file-utf8.json'), 'rb') as f:
        assert json.loads(f.read()) == {'foo': '\u1234'}
