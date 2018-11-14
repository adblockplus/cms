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

from flask import Flask, request, jsonify, Response, send_file

import json

from tests.utils import create_in_memory_zip
from cms.translations.xtm.constants import SUPPORTED_LOCALES

__all__ = [
    'xtm_mock',
    'get_configured_app',
]

_CREDENTIALS = {
    'token_gen_valid': {'client': 'admin', 'password': 'pass', 'userId': 20},
    'token_gen_invalid': {'client': 'user', 'password': 'pass', 'userId': 50},
    'token_valid': 'TheXTM-APIToken-VALID',
    'token_invalid': 'TheXTM-APIToken-INVALID',
}

_PROJECT_IDS = {
    'valid': 1234,
    'invalid': 1111,
    'valid-no-targetfiles': 9999,
}

_CREATION_MANDATORY_KEYS = {'workflowId', 'referenceId', 'name',
                            'targetLanguages', 'customerId', 'description'}

_CREATION_OPTIONAL_KEYS = {r'translationFiles\[(?P<idx>\d+)\].file',
                           r'translationFiles\[(?P<idx>\d+)\].name'}

xtm_mock = Flask('mocking-XTM')


def get_configured_app(**kwargs):
    xtm_mock.config['rootdir'] = kwargs.pop('rootdir', '')
    xtm_mock.config['target_languages'] = kwargs.pop('target_langs', ['de_DE'])
    xtm_mock.config['files'] = kwargs.pop('files', [])
    xtm_mock.config['source_language'] = kwargs.pop('source_lang', 'en_US')
    xtm_mock.config['workflows'] = [
        {'name': 'workflow1', 'id': 2222},
        {'name': 'workflow2', 'id': 3333},
    ]
    return xtm_mock.wsgi_app


def _check_auth():
    try:
        auth = request.headers['Authorization']
    except Exception:
        return False

    if auth != 'XTM-Basic ' + _CREDENTIALS['token_valid']:
        return False

    return True


def _generate_jobs_list():
    jobs = []
    for lng in xtm_mock.config['target_languages']:
        for f in xtm_mock.config['files']:
            jobs.append({
                'fileName': f['name'],
                'jobId': 1,
                'sourceLanguage': xtm_mock.config['source_language'],
                'targetLanguage': lng,
            })

    return jobs


@xtm_mock.route('/rest-api/auth/token', methods=['POST'])
def authenticate():
    if not request.is_json:
        return Response(
            status=400,
            response=json.dumps({'reason': 'Request body not a JSON.'}),
        )

    credentials = request.json
    missing_keys = \
        set(_CREDENTIALS['token_gen_valid'].keys()) - set(credentials.keys())

    if len(missing_keys) > 0:
        return Response(
            status=400,
            response=json.dumps({'reason': 'Missing keys: {}'.format(
                missing_keys)}),
        )

    if credentials == _CREDENTIALS['token_gen_valid']:
        return jsonify({'token': _CREDENTIALS['token_valid']})

    if credentials == _CREDENTIALS['token_gen_invalid']:
        return jsonify({'token': _CREDENTIALS['token_invalid']})

    return Response(
        status=400,
        response=json.dumps({'reason': 'Invalid credentials.'}),
    )


@xtm_mock.route('/rest-api/projects', methods=['POST'])
def create_project():
    if not _check_auth():
        return Response(
            status=401,
            response=json.dumps({'reason': 'Authentication failed.'}),
        )

    form_data = request.form.to_dict(flat=False)
    files = request.files.to_dict()
    xtm_mock.config['target_languages'] = form_data['targetLanguages']
    keys_diff = _CREATION_MANDATORY_KEYS - set(form_data.keys())

    if len(keys_diff) != 0:
        return Response(
            status=400,
            response=json.dumps(
                {'reason': 'Keys missing: {}'.format(keys_diff)},
            ),
        )

    # To make everything easier, just add the 1st file to the class
    if 'translationFiles[0].name' in form_data.keys():
        xtm_mock.config['files'].append({
            'name': form_data['translationFiles[0].name'][0],
            'data': files['translationFiles[0].file'],
        })

    response_json = {
        'name': form_data['name'][0],
        'projectId': _PROJECT_IDS['valid'],
        'jobs': _generate_jobs_list(),
    }

    return Response(status=201, response=json.dumps(response_json))


@xtm_mock.route('/rest-api/projects/<int:project_id>/metrics', methods=['GET'])
def get_metrics(project_id):
    if not _check_auth():
        return Response(
            status=401,
            response=json.dumps({'reason': 'Authentication failed.'}),
        )

    reply = [{
        'coreMetrics': {},
        'jobsMetrics': [],
        'metricsProgress': {},
        'targetLanguage': tl,
    } for tl in xtm_mock.config['target_languages']]

    if project_id == _PROJECT_IDS['valid']:
        return jsonify(reply)

    return Response(status=404, response=json.dumps({'reason': 'Project not '
                                                               'found!'}))


@xtm_mock.route('/rest-api/projects/<int:project_id>/target-languages',
                methods=['POST'])
def add_languages(project_id):
    if not _check_auth():
        return Response(
            status=401,
            response=json.dumps({'reason': 'Authentication failed.'}),
        )
    if not request.is_json:
        return Response(
            status=400,
            response=json.dumps({'reason': 'Not a JSON.'}),
        )

    for language in request.json['targetLanguages']:
        if language not in SUPPORTED_LOCALES:
            return Response(
                status=400,
                response=json.dumps(
                    {'reason': 'Unsupported language: {''}'.format(language)},
                ),
            )

    xtm_mock.config['target_languages'] += request.json['targetLanguages']
    response = {
        'jobs': _generate_jobs_list(),
        'projectId': project_id,
        'projectName': 'test-name',
    }

    if project_id == _PROJECT_IDS['valid']:
        return jsonify(response)

    return Response(
        status=404,
        response=json.dumps({'reason': 'Project not found!'}),
    )


@xtm_mock.route('/rest-api/projects/<int:project_id>/files/upload',
                methods=['POST'])
def upload_and_update(project_id):
    if not _check_auth():
        return Response(
            status=401,
            response='Authentication failed.',
        )
    if project_id == _PROJECT_IDS['invalid']:
        return Response(
            status=404,
            response='Project not found!',
        )

    data = request.form.to_dict()
    files = request.files.to_dict()

    xtm_mock.config['files'].append({
        'name': data['files[0].name'], 'data': files['files[0].file'],
    })

    return jsonify({
        'project_id': 1234,
        'jobs': _generate_jobs_list(),
    })


@xtm_mock.route('/rest-api/projects/<int:project_id>/files/download',
                methods=['GET'])
def download(project_id):
    if not _check_auth():
        return Response(
            status=401,
            response=json.dumps({'reason': 'Authentication failed.'}),
        )
    if project_id == _PROJECT_IDS['invalid']:
        return Response(
            status=404,
            response=json.dumps({'reason': 'Project not found.'}),
        )
    if project_id == _PROJECT_IDS['valid-no-targetfiles']:
        return Response(status=200)

    names = [
        '/'.join([target_lang, f['name']]) for f in xtm_mock.config['files']
        for target_lang in xtm_mock.config['target_languages']
    ]
    data = [
        f['data'] for f in xtm_mock.config['files']
        for _ in xtm_mock.config['target_languages']
    ]

    zip_file = create_in_memory_zip(names, data)
    return send_file(
        zip_file,
        mimetype='application/zip',
    )


@xtm_mock.route('/rest-api/workflows', methods=['GET'])
def get_workflows():
    if not _check_auth():
        return Response(
            status=401,
            response=json.dumps({'reason': 'Authentication failed.'}),
        )

    name = request.args.get('name')
    result = []

    for workflow in xtm_mock.config['workflows']:
        if name in workflow['name']:
            result.append(workflow)

    return jsonify(result)


if __name__ == '__main__':
    xtm_mock.run(debug=True)
