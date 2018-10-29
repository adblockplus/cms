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

"""Script handling interaction with the XTM Cloud REST API."""

import argparse
import logging
import sys
import getpass
import os

from cms.translations.xtm.xtm_api import (
    XTMCloudException, get_token, XTMCloudAPI,
)
import cms.translations.xtm.constants as const
from cms.translations.xtm.projects_handler import (
    create_project, upload_files, download_files,
)
from cms.translations.xtm.utils import input_fn, read_token
from cms.sources import create_source


def handle_projects(args):
    try:
        api = XTMCloudAPI(read_token())
    except Exception as err:
        sys.exit(err)
    with create_source(args.source_dir, cached=True) as fs:
        args.projects_func(args, api, fs)


def generate_token(args):
    """Generate an API token from username and password."""
    username = input_fn('Username: ')
    user_id = input_fn('User ID: ')
    password = getpass.getpass(prompt='Pasword: ')

    logging.info(const.InfoMessages.GENERATING_TOKEN.format(username, user_id))
    try:
        token = get_token(username, password, int(user_id))
        logging.info(const.InfoMessages.TOKEN_GENERATED.format(token))

        cmd = const.Token.SAVE_COMMAND.format(const.Token.ENV_VAR, token)
        sys.stdout.write(const.InfoMessages.TOKEN_SAVE_TO_ENV_VAR.format(cmd))
    except XTMCloudException as err:
        sys.exit(err)
    except Exception as err:
        sys.exit(err)


def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    #  Universal arguments
    parser.add_argument('-v', '--verbose', action='store_true',
                        help=const.ArgumentsHelp.VERBOSE)

    #  Subparser for generating token
    token_parser = subparsers.add_parser('login',
                                         help=const.ArgumentsHelp.LOGIN)
    token_parser.set_defaults(func=generate_token)

    #  Subparser for project creation.
    project_create_parser = subparsers.add_parser(
        'create',
        help=const.ArgumentsHelp.ProjectCreate.MAIN,
    )
    project_create_parser.set_defaults(func=handle_projects)
    project_create_parser.set_defaults(projects_func=create_project)

    project_create_parser.add_argument(
        'source_dir', help=const.ArgumentsHelp.PROJECT_SOURCE_DIR,
        default=os.getcwd(), nargs='?',
    )

    project_create_parser.add_argument(
        '--name', required=True,
        help=const.ArgumentsHelp.ProjectCreate.NAME,
    )
    project_create_parser.add_argument(
        '--desc', required=True,
        help=const.ArgumentsHelp.ProjectCreate.DESC,
    )

    project_create_parser.add_argument(
        '--client-id', required=True, type=int,
        help=const.ArgumentsHelp.ProjectCreate.CLIENT_ID,
    )
    project_create_parser.add_argument(
        '--ref-id', required=True,
        help=const.ArgumentsHelp.ProjectCreate.REF_ID,
    )
    project_create_parser.add_argument(
        '--workflow-id', type=int,
        help=const.ArgumentsHelp.ProjectCreate.WORKFLOW_ID,
    )
    project_create_parser.add_argument(
        '--source-lang', default='en_US',
        help=const.ArgumentsHelp.ProjectCreate.SOURCE,
    )
    project_create_parser.add_argument(
        '--save-id', action='store_true', default=False,
        help=const.ArgumentsHelp.ProjectCreate.SAVE_ID,
    )
    project_create_parser.add_argument(
        '--workflow-name',
        help=const.ArgumentsHelp.ProjectCreate.WORKFLOW_NAME,
    )

    #  Subparser for uploading files to project
    project_upload_parser = subparsers.add_parser(
        'upload', help=const.ArgumentsHelp.ProjectUpload.MAIN,
    )
    project_upload_parser.set_defaults(func=handle_projects)
    project_upload_parser.set_defaults(projects_func=upload_files)

    project_upload_parser.add_argument(
        'source_dir', help=const.ArgumentsHelp.PROJECT_SOURCE_DIR,
        default=os.getcwd(), nargs='?',
    )

    project_upload_parser.add_argument(
        '--no-overwrite', action='store_true', default=False,
        help=const.ArgumentsHelp.ProjectUpload.NO_OVERWRITE,
    )

    # Subparser for downloading files from project
    download_parser = subparsers.add_parser(
        'download', help=const.ArgumentsHelp.PROJECT_DOWNLOAD,
    )
    download_parser.set_defaults(func=handle_projects)
    download_parser.set_defaults(projects_func=download_files)

    download_parser.add_argument(
        'source_dir', help=const.ArgumentsHelp.PROJECT_SOURCE_DIR,
        default=os.getcwd(), nargs='?',
    )

    return parser.parse_args()


def main():
    """Run XTM integration script."""
    args = parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    args.func(args)


if __name__ == '__main__':
    main()
