import os

from flask import Flask, send_from_directory, jsonify, request

app = Flask('mock_api')


def load(rootdir, zipdir):
    app.request_log = []
    app.config['zipdir'] = zipdir
    app.config['info'] = {'files': [], 'languages': []}
    app.config['supported_languages'] = []

    for root, locales, files in os.walk(rootdir):
        for locale in locales:
            files = []
            app.config['supported_languages'].append({'crowdin_code': locale})
            app.config['info']['languages'].append({
                'code': locale,
                'can_translate': 1,
                'can_approve': 1,
            })

            for translations in os.listdir(os.path.join(root, locale)):
                files.append({'name': translations, 'node_type': 'file'})

            app.config['info']['files'].append({
                'name': locale,
                'files': files,
                'node_type': 'directory',
            })

    return app


@app.before_request
def log_request_info():
    app.request_log.append((request.url, str(request.get_data())))


@app.route('/api/project/test/info', methods=['GET'])
def info():
    return jsonify(app.config['info'])


@app.route('/api/project/test/edit-project', methods=['POST'])
def edit():
    return jsonify()


@app.route('/api/project/test/supported-languages', methods=['GET'])
def supported_langs():
    return jsonify(app.config['supported_languages'])


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
    return send_from_directory(app.config['zipdir'], 'all.zip')
