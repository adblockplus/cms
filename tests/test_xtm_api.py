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

"""Tests for the XTM API integration."""

from __future__ import unicode_literals

import json
import zipfile
from io import BytesIO

import pytest

from cms.translations.xtm.xtm_api import (XTMCloudException, XTMCloudAPI,
                                          get_token)
from tests.utils import exception_test

_VALID_TOKEN = 'TheXTM-APIToken-VALID'
_INVALID_TOKEN = 'TheXTM-APIToken-INVALID'

_FILES_UPLOAD = {'test.json': json.dumps({'foo': 'bar'})}
_EXPECTED_JOBS = [{'fileName': 'test.json', 'jobId': 1,
                   'sourceLanguage': 'en_US', 'targetLanguage': 'de_DE'}]


@pytest.mark.parametrize('credentials,is_ok,err_msg, exp_token', [
    (['admin', 'pass', 20], True, None, 'TheXTM-APIToken-VALID'),
    (['admin', 'wrong_pass', 20], False, 'Invalid credentials.', None),
])
def test_token_generation(intercept, credentials, is_ok, err_msg, exp_token):
    """Test the API token generation."""
    if is_ok:
        token = get_token(*credentials)
        assert token == exp_token
    else:
        exception_test(get_token, XTMCloudException, err_msg, *credentials)


@pytest.mark.parametrize('token,args,files,exp_msg,exp_jobs', [
    (_VALID_TOKEN, ['name', 'description', 'ref_id', ['en_US'], 10, 20], None,
     None, []),
    (_INVALID_TOKEN, ['name', 'description', 'ref_id', ['en_US'], 10, 20],
     None, 'Authentication failed.', []),
    (_VALID_TOKEN, ['name', 'description', 'ref_id', ['de_DE'], 10, 20],
     _FILES_UPLOAD, None, _EXPECTED_JOBS),
])
def test_project_creation(intercept, token, files, args, exp_msg, exp_jobs):
    """Test creation of files behaves appropriately."""
    api = XTMCloudAPI(token)

    if exp_msg:
        exception_test(api.create_project, XTMCloudException, exp_msg, *args)
    else:
        project_id, jobs = api.create_project(*args, files=files)
        assert project_id == 1234
        assert exp_jobs == jobs


@pytest.mark.parametrize('token,project_id,exp_langs,exp_msg', [
    (_VALID_TOKEN, 1234, {'de_DE'}, None),
    (_INVALID_TOKEN, 1234, None, 'Authentication failed.'),
    (_VALID_TOKEN, 1111, None, 'Project not found!'),
])
def test_extracting_target_languages(intercept, token, project_id,
                                     exp_langs, exp_msg):
    """Test extraction of target languages."""
    api = XTMCloudAPI(token)

    if exp_msg:
        exception_test(api.get_target_languages, XTMCloudException, exp_msg,
                       project_id)
    else:
        langs = api.get_target_languages(project_id)

        assert exp_langs == langs


@pytest.mark.parametrize('token,project_id,new_langs,exp_msg', [
    (_VALID_TOKEN, 1234, ['en_GB'], None),
    (_INVALID_TOKEN, 1234, ['en_GB'], 'Authentication failed.'),
    (_VALID_TOKEN, 1111, ['en_GB'], 'Project not found!'),
    (_VALID_TOKEN, 1234, ['foo_BAR'], 'Unsupported language: foo_BAR'),
])
def test_adding_target_language(intercept, token, project_id, new_langs,
                                exp_msg):
    """Test adding target languages."""
    api = XTMCloudAPI(token)

    if exp_msg:
        exception_test(api.add_target_languages, XTMCloudException, exp_msg,
                       project_id, new_langs)
    else:
        api.add_target_languages(project_id, new_langs)


@pytest.mark.parametrize('token,project_id,exp_msg,', [
    (_INVALID_TOKEN, 1234, 'Authentication failed'),
    (_VALID_TOKEN, 1111, 'Project not found'),
    (_VALID_TOKEN, 1234, None),
])
def test_file_download(intercept_populated, token, project_id, exp_msg):
    """Test file downloading."""
    api = XTMCloudAPI(token)

    if exp_msg:
        exception_test(api.download_files, XTMCloudException, exp_msg,
                       project_id)
    else:
        contents = api.download_files(project_id)
        zipfile.ZipFile(BytesIO(contents))


@pytest.mark.parametrize('token,project_id,files,exp_err,exp_msg,exp_jobs', [
    (_VALID_TOKEN, 1234, [], Exception, 'No files provided for upload.', []),
    (_INVALID_TOKEN, 1234, _FILES_UPLOAD, XTMCloudException, 'Authentication '
                                                             'failed', []),
    (_VALID_TOKEN, 1111, _FILES_UPLOAD, XTMCloudException, 'Project not '
                                                           'found', []),
    (_VALID_TOKEN, 1234, _FILES_UPLOAD, None, None, _EXPECTED_JOBS),
])
def test_file_upload(intercept, token, project_id, files, exp_err, exp_msg,
                     exp_jobs):
    """Test file uploading."""
    api = XTMCloudAPI(token)
    if exp_msg is not None:
        exception_test(api.upload_files, exp_err, exp_msg, files, project_id)
    else:
        assert exp_jobs == api.upload_files(files, project_id)


@pytest.mark.parametrize('token,name,exp_err,exp_msg,exp_ids', [
    (_INVALID_TOKEN, 'foo', XTMCloudException, 'Authentication failed', None),
    (_VALID_TOKEN, 'workflow', None, None, []),
    (_VALID_TOKEN, 'workflow1', None, None, [2222]),
])
def test_workflow_id_extraction(intercept, token, name, exp_err,
                                exp_msg, exp_ids):
    api = XTMCloudAPI(token)
    if exp_msg is not None:
        exception_test(api.get_workflows_by_name, exp_err, exp_msg, name)
    else:
        assert exp_ids == api.get_workflows_by_name(name)
