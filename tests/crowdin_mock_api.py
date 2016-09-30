from flask import Flask, send_from_directory, jsonify, request

app = Flask(__name__)
app.request_log = []


@app.before_request
def log_request_info():
    log = (request.url, str(request.get_data()))
    app.request_log.append(log)


@app.route('/api/project/test/info', methods=['GET'])
def info():
    return jsonify(
        {
            'languages': [
                {
                    'name': 'German',
                    'code': 'de',
                    'can_translate': 1,
                    'can_approve': 1,

                },
                {
                    'name': 'English',
                    'code': 'en',
                    'can_translate': 1,
                    'can_approve': 1,

                },

            ],
            'files': [
                {
                    'node_type': 'directory',
                    'name': 'en',
                    'files': [
                        {
                            'node_type': 'file',
                            'name': 'translate.json',
                            'created': '2016-09-26 08:30:07',
                            'last_updated': '2016-09-26 08:30:08',
                            'last_accessed': None,
                            'last_revision': '1'
                        },
                    ]
                },
                {
                    'node_type': 'directory',
                    'name': 'de',
                    'files': [
                        {
                            'node_type': 'file',
                            'name': 'translate.json',
                            'created': '2016-09-26 08:30:07',
                            'last_updated': '2016-09-26 08:30:08',
                            'last_accessed': None,
                            'last_revision': '1'
                        }
                    ]
                }
            ]
        }
    )


@app.route('/api/project/test/supported-languages', methods=['GET'])
def supported_langs():
    return jsonify(
        [
            {
                'name': 'German',
                'crowdin_code': 'de',
                'editor_code': 'de',
                'iso_639_1': 'de',
                'iso_639_3': 'deu',
                'locale': 'de-DE'
            },
            {
                'name': 'English',
                'crowdin_code': 'en',
                'editor_code': 'en',
                'iso_639_1': 'en',
                'iso_639_3': 'eng',
                'locale': 'en-US'
            },
        ]
    )


@app.route('/api/project/test/add-file', methods=['POST'])
def add_file():
    app.string = request.get_data()
    return jsonify()


@app.route('/api/project/test/upload-translation', methods=['POST'])
def upload_translation():
    return jsonify()


@app.route('/api/project/test/delete-directory', methods=['POST'])
def delete_directory():
    return jsonify()


@app.route('/api/project/test/delete-file', methods=['POST'])
def delete_file():
    return jsonify()


@app.route('/api/project/test/export', methods=['GET'])
def export():
    return jsonify({'success': {'status': 'skipped'}})


@app.route('/api/project/test/download/all.zip', methods=['GET'])
def get_zip():
    return send_from_directory('', 'all.zip')
