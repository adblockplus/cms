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

import requests

__all__ = [
    'XTMCloudAPI', 'XTMCloudException', 'get_token',
]

_BASE_URL = 'https://wstest2.xtm-intl.com/rest-api/'


class XTMCloudException(Exception):
    _BASE_MESSAGE = ('Error: XTM Cloud API failed while {0}, with error '
                     'code {1}: {2}')

    def __init__(self, code, msg, action):
        """Constructor.

        Parameters
        ----------
        code: int
            The error code returned by the API.
        msg: str
            The error message returned by the API.
        action: str
            The action that caused the exception.

        """
        full_message = self._BASE_MESSAGE.format(action, code, msg)
        super(XTMCloudException, self).__init__(full_message)

        self.code = code
        self.message = msg
        self.action = action


class XTMCloudAPI(object):

    _AUTHORIZATION_TMP = 'XTM-Basic {0}'

    class _UrlPaths:
        CREATE = 'projects'
        DOWNLOAD = 'projects/{0}/files/download'
        UPLOAD = 'projects/{0}/files/upload'
        GET_TARGET_LANG = 'projects/{0}/metrics'
        ADD_TARGET_LANG = 'projects/{0}/target-languages'
        GET_WORKFLOW_IDS = 'workflows'

    _MATCH_TYPE = {
        False: 'NO_MATCH',
        True: 'MATCH_NAMES',
    }

    class _SuccessCodes:
        CREATE = 201
        UPLOAD = 200
        DOWNLOAD = 200
        GET_TARGET_LANGS = 200
        ADD_TARGET_LANGS = 200
        GET_WORKFLOW_IDS = 200

    def __init__(self, token):
        """Constructor.

        Parameters
        ----------
        token: str
            Token used to authenticate with the API.

        """
        self._token = token
        self.base_url = _BASE_URL

    def _execute(self, url, data=None, files=None, stream=False,
                 params=None, headers=None):
        """Send request to the API and return the response.

        Parameters
        ----------
        url: str
            The url we're making the request to.
        data: dict
            The data to be sent to the API. If provided, the request will be
            a POST request, otherwise GET. Default None.
        files: dict
            The files to be uploaded(if any). Default None.
        params: dict
            The URL parameters to be specified.
        stream: bool
            Whether using the stream option when executing the request or not.
        headers: dict
            Default headers to be sent with the request.

        Returns
        -------
        The contents of the API response.

        """
        auth_header = {
            'Authorization': self._AUTHORIZATION_TMP.format(self._token),
        }

        if headers:
            headers.update(auth_header)
        else:
            headers = auth_header

        if data:
            response = requests.post(url, data=data, files=files,
                                     headers=headers, params=params,
                                     stream=stream)
        else:
            response = requests.get(url, headers=headers, stream=True,
                                    params=params)

        return response

    def _construct_files_dict(self, files, param_tmp):
        """Convert a list of files to an uploadable format.

        Parameters
        ----------
        files: iterable
            Of the files to be uploaded. See create_project() for expected
            format.

        Returns
        -------
        dict
            With the names of the files to be uploaded.
        dict
            With the files in the correct format for upload.

        """
        files_data = {}
        file_names = {}
        idx = 0

        for name in files:
            file_names[(param_tmp + '.name').format(idx)] = name
            files_data[(param_tmp + '.file').format(idx)] = files[name]
            idx += 1

        return file_names, files_data

    def create_project(self, name, description, reference_id, target_languages,
                       customer_id, workflow_id, source_language='en_US',
                       files=None):
        """Create a new project with XTM Cloud.

        Parameters
        ----------
        name: str
            The name of the project we want to create.
        description: str
            The description of the project.
        reference_id: str
            The referenceID of the project.
        target_languages: iterable
            The target language(s) for the project.
        customer_id: int
            The id of the customer creating the project
        workflow_id: int
            The id of the main workflow
        source_language: str
            The source language for the project.
        files: dict
            With the files to be uploaded on creation.
            Expects this format:
                <file_name>: <file_data>

        Returns
        -------
        int
            The id of the created project.
        iterable
            Containing the information for all the jobs that were initiated.
            See docs for upload_files() for the fully documented format.

        Raises
        ------
        XTMCloudException
            If the creation of the project was not successful.

        """
        data = {
            'name': name,
            'description': description,
            'referenceId': reference_id,
            'customerId': customer_id,
            'workflowId': workflow_id,
            'sourceLanguage': source_language,
            'targetLanguages': target_languages,
        }

        if files:
            file_names, files_to_upload = self._construct_files_dict(
                files, 'translationFiles[{}]')
            data.update(file_names)
        else:
            # Hacky way to go around 415 error code
            files_to_upload = {'a': 'b'}

        url = self.base_url + self._UrlPaths.CREATE

        response = self._execute(url, data=data, files=files_to_upload)

        if response.status_code != self._SuccessCodes.CREATE:
            # The creation was not successful
            raise XTMCloudException(response.status_code,
                                    response.text.decode('utf-8'),
                                    'creating job')

        data = json.loads(response.text.encode('utf-8'))

        return data['projectId'], data['jobs']

    def upload_files(self, files, project_id, overwrite=True):
        """Upload a set of files to a project.

        Parameters
        ----------
        files: dict
            With the files to be uploaded on creation.
            Expects this format:
                <file_name>: <file_data>
        project_id: int
            The id of the project we're uploading to.
        overwrite: bool
            Whether the files to be uploaded are going to overwrite the files
            that are already in the XTM project or not. Default False.

        Returns
        -------
        iterable
            With the upload results. Each element will have the form:

                {
                    'fileName': <the name of the uploaded file>,
                    'jobId': <ID of the job associated with the file>,
                    'sourceLanguage': <source language of the uploaded file>,
                    'targetLanguage': <target language of the uploaded file>,
                }

        Raises
        ------
        XTMCloudException
            If the API operation fails.

        """
        file_names, files_to_upload = self._construct_files_dict(
            files, 'files[{}]',
        )

        if len(files_to_upload.keys()) == 0:
            raise Exception('Error: No files provided for upload.')

        data = {'matchType': self._MATCH_TYPE[overwrite]}
        data.update(file_names)

        url = self.base_url + self._UrlPaths.UPLOAD.format(project_id)

        response = self._execute(url, data=data, files=files_to_upload)

        if response.status_code != self._SuccessCodes.UPLOAD:
            raise XTMCloudException(response.status_code,
                                    response.text.encode('utf-8'),
                                    'uploading files')

        return json.loads(response.text.encode('utf-8'))['jobs']

    def download_files(self, project_id, files_type='TARGET'):
        """Download files for a specific project.

        Parameters
        ----------
        project_id: int
            The id of the project to download from.
        files_type: str
            The type of the files we want to download. Default TARGET

        Returns
        -------
        bytes
            The contents of the zip file returned by the API

        Raises
        ------
        XTMCloudException
            If the request is flawed in any way.

        """
        url = (self.base_url + self._UrlPaths.DOWNLOAD).format(project_id)

        exception_msg = {
            400: 'Invalid request',
            401: 'Authentication failed',
            500: 'Internal server error',
            404: 'Project not found.',
        }

        response = self._execute(url, params={'fileType': files_type},
                                 stream=True)

        if response.status_code != self._SuccessCodes.DOWNLOAD:
            raise XTMCloudException(
                response.status_code,
                exception_msg[response.status_code],
                'downloading files from {}'.format(project_id),
            )

        return response.content

    def get_target_languages(self, project_id):
        """Get all the target languages for a specific project.

        Parameters
        ----------
        project_id: int
            The id if the project in question.

        Returns
        -------
        iterable
            With the target languages for this project.

        Raises
        ------
        XTMCloudException
            If the request is unsuccessful.

        """
        url = (self.base_url + self._UrlPaths.GET_TARGET_LANG).format(
            project_id,
        )

        response = self._execute(url, stream=True)

        if response.status_code != self._SuccessCodes.GET_TARGET_LANGS:
            raise XTMCloudException(response.status_code, response.content,
                                    'extracting target languages')

        data = json.loads(response.content.encode('utf-8'))
        return {item['targetLanguage'] for item in data}

    def add_target_languages(self, project_id, target_languages):
        """Add target languages to a project.

        Parameters
        ----------
        project_id: int
            The id of the project in question.
        target_languages: iterable
            The languages to be added.

        Raises
        -------
        XTMCloudException
            If the request to the API was not successful.

        """
        data = json.dumps({
            'targetLanguages': target_languages,
        })
        url = (self.base_url + self._UrlPaths.ADD_TARGET_LANG).format(
            project_id,
        )
        headers = {'content-type': 'application/json'}

        response = self._execute(url, data=data, headers=headers)

        if response.status_code != self._SuccessCodes.ADD_TARGET_LANGS:
            raise XTMCloudException(response.status_code, response.content,
                                    'adding target languages to project')

    def get_workflows_by_name(self, name):
        """Get workflows with a specific name.

        Parameters
        ----------
        name: str
            The name of the workflow we're looking for.

        Returns
        -------
        iterable
            Of workflow ids that match the name provided.

        """
        url = self.base_url + self._UrlPaths.GET_WORKFLOW_IDS

        response = self._execute(url, params={'name': name})

        if response.status_code != self._SuccessCodes.GET_WORKFLOW_IDS:
            raise XTMCloudException(response.status_code, response.content,
                                    'extracting workflow ids')

        valid_ids = []
        for item in json.loads(response.content.encode('utf-8')):
            if name.lower().replace(' ', '') == \
                    item['name'].lower().replace(' ', ''):
                valid_ids.append(item['id'])
        return valid_ids


def get_token(username, password, user_id):
    """Generate an API token from username and password.

    Parameters
    ----------
    username: str
        The username used to generate the token.
    password: str
        The password used to generate the token.
    user_id: int
        The user ID used to generate the token.

    Returns
    -------
    str
        The resulting token generated by the API.

    Raises
    ------
    XTMCloudException
        If the credentials provided were invalid.

    """
    request_body = json.dumps({
        'client': username,
        'password': password,
        'userId': user_id,
    })

    url = _BASE_URL + 'auth/token'

    headers = {'content-type': 'application/json'}

    response = requests.post(url, data=request_body, headers=headers)

    if response.status_code == 200:
        return json.loads(response.text)['token'].encode()

    raise XTMCloudException(response.status_code,
                            response.text.encode('utf-8'),
                            'generating token')
