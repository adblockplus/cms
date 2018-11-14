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

import collections
import logging
import os
import time
import json

from cms.utils import process_page
import cms.translations.xtm.constants as const
from cms.translations.xtm.xtm_api import XTMCloudException


__all__ = [
    'extract_strings', 'resolve_locales', 'map_locales', 'local_to_remote',
    'remote_to_local', 'run_and_wait', 'sanitize_project_name', 'read_token',
    'get_files_to_upload', 'log_resulting_jobs', 'clear_files', 'input_fn',
]


def log_resulting_jobs(jobs):
    """Log the jobs created as a result of uploading files/ creating projects.

    Parameters
    ----------
    jobs: iterable
        Of dicts, as returned by XTM.

    """
    if len(jobs) == 0:
        logging.info(const.InfoMessages.NO_JOBS_CREATED)
        return

    for job in jobs:
        logging.info(
            const.InfoMessages.CREATED_JOB.format(
                job['jobId'], job['fileName'], job['targetLanguage'],
            ),
        )


def get_files_to_upload(source):
    """Return the files to upload in the format supported by XTMCloudAPI.

    It performs the following tasks:
        1. Extracts the translation strings from the website.
        2. Cleanup the extracted strings (i.e. ignore all empty ones).
        3. Convert local file names to remote ones.
        4. Construct a dictionary with the format required by XTMCloudAPI

    Parameters
    ----------
    source: cms.sources.Source

    Returns
    -------
    dict
        With the following format:
        <remote_filename>: <file_data>

    """
    # 1. Extracting strings.
    raw_strings = extract_strings(source)
    page_strings = {}

    # 2. Cleaning up.
    for page, string in raw_strings.iteritems():
        if string:
            page_strings[page] = string

    # 3. Converting local file names.
    remote_names = local_to_remote(page_strings)

    # 4. Constructing final data structure
    files_to_upload = {}
    for file in remote_names:
        files_to_upload[remote_names[file]] = json.dumps(page_strings[file])

    return files_to_upload


def read_token():
    """Read token from pre-defined environment variable."""
    token = os.environ.get(const.Token.ENV_VAR)
    if token:
        return token

    raise Exception(const.ErrorMessages.NO_TOKEN_PROVIDED.format(
        const.Token.CREATION_CMD,
    ))


def sanitize_project_name(name):
    """Handle project name conflicts.

    Parameters
    ----------
    name: str
        The name of the project.

    Returns
    -------
    str
        The new name of the project, with the length cut down to
        const.ProjectName.MAX_LENGTH and invalid characters replaced with
        const.ProjectName.NAME_WILDCARD.

    """
    valid_name = ''.join(
        [const.ProjectName.NAME_WILDCARD
         if c in const.ProjectName.INVALID_CHARS else c for c in name],
    )

    return valid_name[:const.ProjectName.MAX_LENGTH]


def extract_strings(source):
    """Extract strings from a website.

    Parameters
    ----------
    source: cms.sources.Source
        The source representing the website.

    Returns
    -------
    dict
        With the extracted strings.

    """
    logging.info(const.InfoMessages.EXTRACTING_STRINGS)
    page_strings = collections.defaultdict(collections.OrderedDict)

    defaultlocale = source.read_config().get(
        const.Config.MAIN_SECTION, const.Config.DEFAULT_LOCALE_OPTION,
    )

    def record_string(page, locale, name, value, comment, fixed_strings):
        if locale != defaultlocale:
            return

        store = page_strings[page]
        store[name] = {'message': value}

        if fixed_strings:
            comment = comment + '\n' if comment else ''
            comment += ', '.join('{{{0}}}: {1}'.format(*i_s)
                                 for i_s in enumerate(fixed_strings, 1))
        if comment:
            store[name]['description'] = comment

    for page, page_format in source.list_pages():
        process_page(source, defaultlocale, page, format=page_format,
                     localized_string_callback=record_string)

    return page_strings


def resolve_locales(api, source):
    """Sync a website's locales with the target languages of the API.

    Parameters
    ----------
    api: cms.bin.xtm_translations.xtm_api.XTMCloudAPI
        Handler used to make requests to the API.
    source: cms.sources.Source
        Source representing a website.

    """
    logging.info(const.InfoMessages.RESOLVING_LOCALES)
    local_locales = map_locales(source)
    project_id = source.read_config().get(
        const.Config.XTM_SECTION, const.Config.PROJECT_OPTION,
    )

    languages = run_and_wait(
        api.get_target_languages,
        XTMCloudException,
        const.UNDER_ANALYSIS_MESSAGE,
        const.InfoMessages.WAITING_FOR_PROJECT,
        project_id=project_id,
    )

    enabled_locales = {l.encode('utf-8') for l in languages}

    if len(enabled_locales - local_locales) != 0:
        raise Exception(const.ErrorMessages.LOCALES_NOT_PRESENT.format(
            enabled_locales - local_locales, project_id,
        ))

    if not local_locales == enabled_locales:
        # Add languages to the project
        langs_to_add = list(local_locales - enabled_locales)
        logging.info(const.InfoMessages.ADDING_LANGUAGES.format(
            project_id, langs_to_add,
        ))
        run_and_wait(
            api.add_target_languages,
            XTMCloudException,
            const.UNDER_ANALYSIS_MESSAGE,
            const.InfoMessages.WAITING_FOR_PROJECT,
            project_id=project_id,
            target_languages=langs_to_add,
        )


def map_locales(source):
    """Map website locale to target languages supported by XTM.

    Parameters
    ----------
    source: cms.sources.Source
        Source representing a website.

    Returns
    -------
    set
        Of the resulting mapped locales.

    """
    config = source.read_config()
    defaultlocale = config.get(const.Config.MAIN_SECTION,
                               const.Config.DEFAULT_LOCALE_OPTION)
    locales = source.list_locales() - {defaultlocale}

    mapped_locales = set()

    for locale in locales:
        if locale in const.SUPPORTED_LOCALES:
            mapped_locales.add(locale)
        else:
            xtm_locale = '{0}_{1}'.format(locale, locale.upper())
            if xtm_locale in const.SUPPORTED_LOCALES:
                mapped_locales.add(xtm_locale)
            else:
                logging.warning(
                    const.WarningMessages.LOCALE_NOT_SUPPORTED.format(locale),
                )

    return mapped_locales


def local_to_remote(local_names):
    """Convert local file names to valid remote ones.

    Parameters
    ----------
    local_names: iterable
        The local file names (without any extension).

    Returns
    -------
    dict
       With the local files. Each element in the set is a tuple with the
       format:
            <local_filename>: <remote_filename>

    """
    files = {}

    for page in local_names:
        remote_name = '{}.json'.format(
            page.replace(os.path.sep, const.FileNames.PATH_SEP_REP),
        )
        if len(remote_name) > const.FileNames.MAX_LENGTH:
            raise Exception(
                const.ErrorMessages.FILENAME_TOO_LONG.format(
                    '{}.json'.format(page), const.FileNames.MAX_LENGTH,
                ))
        files[page] = remote_name

    return files


def remote_to_local(filename, source_dir, locales):
    """Parse a remote filename and construct a local filesystem name.

    Parameters
    ----------
    filename: str
        The remote filename.
    source_dir: str
        The path to the source directory of the file.
    locales: iterator
        Of local language directories.

    Returns
    -------
    str
        The full path of the file.

    """
    path_elements = filename.split(const.FileNames.PATH_SEP_REP)
    if path_elements[0] == '':
        path_elements = path_elements[1:]
    if path_elements[0] not in locales:
        candidate_locale = path_elements[0].split('_')[0]
        if candidate_locale not in locales:
            raise Exception(
                const.ErrorMessages.CANT_RESOLVE_REMOTE_LANG.format(
                    path_elements[0],
                ),
            )

        path_elements[0] = ''.join([
            candidate_locale,
            path_elements[0].split('_')[1][len(candidate_locale):],
        ])

    return os.path.join(source_dir, *path_elements)


def run_and_wait(func, exc, err_msg, user_msg=None, retry_delay=1,
                 retries=10, **kw):
    """Run a function and, if a specific exception occurs, try again.

    Tries to run the function, and if an exception with a specific message
    is raised, it sleeps and tries again.
    Parameters
    ----------
    func: function
        The function to be run.
    retry_delay: int
        The amount of time to wait on this specific run (in seconds).
    exc: Exception
        The exception we expect to be raised.
    err_msg: str
        The message we expect to be in the exception.
    user_msg: str
        Message to be displayed to the user if we waited for more than 3 steps.
    retries: int
        The number of retries left until actually raising the exception.
    kw: dict
        The keyword arguments for the function.

    Returns
    -------
        The return result of the function.

    """
    if retries == 7 and user_msg:
        logging.info(user_msg)
    try:
        result = func(**kw)
        return result
    except exc as err:
        if retries == 0:
            raise
        if err_msg in str(err):
            time.sleep(retry_delay)
            return run_and_wait(
                func, exc, err_msg, user_msg,
                min(retry_delay * 2, const.MAX_WAIT_TIME), retries - 1, **kw
            )
        raise


def clear_files(dir_path, required_locales, extension='.json'):
    """Delete translation files with a specific extension from dir_path.

    Parameters
    ----------
    dir_path: str
        Path to the root of the subtree we want to delete the files from.
    required_locales: iterable
        Only directories form required_locales will be included
    extension: str
        The extension of the files to delete.

    """
    for root, dirs, files in os.walk(dir_path, topdown=True):
        if root == dir_path:
            dirs[:] = [d for d in dirs if d in required_locales]
        for f in files:
            if f.lower().endswith(extension.lower()):
                os.remove(os.path.join(root, f))


def get_locales(path, default):
    """List the locales available in a website.

    It will exclude the default language from the list.

    Parameters
    ----------
    path: str
        The path to the locales directory.
    default: str
        The default language for the website.

    Returns
    -------
    iterable
        Of the available locales.

    """
    full_contents = os.listdir(path)

    return [
        d for d in full_contents
        if os.path.isdir(os.path.join(path, d)) and d != default
    ]


def write_to_file(data, file_path):
    """Write data to a given file path.

    If the directory path does not exist, then it will be created by default.

    Parameters
    ----------
    data: bytes
        The data to be written to the file.
    file_path: str
        The path of the file we want to write.

    """
    dirs_path = os.path.join(*os.path.split(file_path)[:-1])
    if not os.path.isdir(dirs_path):
        os.makedirs(dirs_path)

    with open(file_path, 'wb') as f:
        f.write(data)


def input_fn(text):
    try:
        return raw_input(text)
    except Exception:
        return input(text)


def extract_workflow_id(api, args):
    """Extract the workflow id, using the arguments provided by the user.

    Parameters
    ----------
    api: XTMCloudAPI
        Used to interact with the XTM API.
    args: argparse.Namespace
        With the arguments provided to the script.

    Returns
    -------
    int
        With the corresponding workflow id.

    Raises
    ------
    XTMCloudException
        If the API communication fails in any way.
    Exception
        In one of the following situations:
            1. If both `--workflow-id` and `--workflow-name` are provided.
            2. If none of the parameters above are provided.
            3. If there are no workflows associated with a given name.

    """
    if args.workflow_id and args.workflow_name:
        raise Exception(const.ErrorMessages.WORKFLOW_NAME_AND_ID_PROVIDED)

    if not (args.workflow_id or args.workflow_name):
        raise Exception(const.ErrorMessages.NO_WORKFLOW_INFO)

    if args.workflow_id:
        return args.workflow_id

    possible_ids = api.get_workflows_by_name(args.workflow_name)

    if len(possible_ids) == 0:
        raise Exception(const.ErrorMessages.NO_WORKFLOW_FOR_NAME.format(
            args.workflow_name))

    return possible_ids[0]
