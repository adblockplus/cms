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

import sys
import logging
import ConfigParser
import zipfile
from io import BytesIO

import cms.translations.xtm.constants as const
from cms.translations.xtm.xtm_api import XTMCloudException
from cms.translations.xtm import utils

__all__ = [
    'create_project', 'upload_files', 'download_files',
]


def create_project(args, api, source):
    """Create a project.

    Parameters
    ----------
    args: argparse.Namespace
        The arguments parsed by the main script.
    api: XTMCloudAPI
        Used for interacting with the project.
    source: FileSource
        Representing the website the project is created for.

    """
    config = source.read_config()

    try:
        project_id = config.get(const.Config.XTM_SECTION,
                                const.Config.PROJECT_OPTION)
        sys.exit(const.ErrorMessages.PROJECT_EXISTS.format(project_id))
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        pass

    target_langs = utils.map_locales(source)

    files_to_upload = utils.get_files_to_upload(source)

    try:
        name = utils.sanitize_project_name(args.name)
        logging.info(const.InfoMessages.PROJECT_NAME_CREATING.format(name))
        logging.info(
            const.InfoMessages.UPLOADING_FILES.format(len(files_to_upload)),
        )

        project_id, resulting_jobs = utils.run_and_wait(
            api.create_project,
            XTMCloudException,
            const.UNDER_ANALYSIS_MESSAGE,
            const.InfoMessages.WAITING_FOR_PROJECT,
            name=name,
            description=args.desc,
            reference_id=args.ref_id,
            target_languages=target_langs,
            customer_id=args.client_id,
            workflow_id=utils.extract_workflow_id(api, args),
            source_language=args.source_lang,
            files=files_to_upload,
        )
    except Exception as err:
        sys.exit(err)

    logging.info(const.InfoMessages.PROJECT_CREATED.format(project_id))
    utils.log_resulting_jobs(resulting_jobs)

    if args.save_id:
        source.write_to_config(
            const.Config.XTM_SECTION,
            const.Config.PROJECT_OPTION,
            str(project_id),
        )
        logging.info(const.InfoMessages.SAVED_PROJECT_ID)


def upload_files(args, api, source):
    """Upload files to project.

    Parameters
    ----------
    args: argparse.Namespace
        The arguments parsed by the main script.
    api: XTMCloudAPI
        Used for interacting with the project.
    source: cms.sources.FileSource
        Representing the website the project is created for.

    """
    config = source.read_config()
    try:
        project_id = config.get(const.Config.XTM_SECTION,
                                const.Config.PROJECT_OPTION)
    except ConfigParser.NoOptionError, ConfigParser.NoSectionError:
        sys.exit(const.ErrorMessages.NO_PROJECT.format(source.get_path('')))

    files_to_upload = utils.get_files_to_upload(source)
    logging.info(
        const.InfoMessages.UPLOADING_FILES.format(len(files_to_upload)),
    )
    try:
        utils.resolve_locales(api, source)

        new_jobs = utils.run_and_wait(
            api.upload_files,
            XTMCloudException,
            const.UNDER_ANALYSIS_MESSAGE,
            const.InfoMessages.WAITING_FOR_PROJECT,
            files=files_to_upload,
            project_id=project_id,
            overwrite=not args.no_overwrite,
        )

        logging.info(const.InfoMessages.FILES_UPLOADED)
        utils.log_resulting_jobs(new_jobs)
    except XTMCloudException as err:
        sys.exit(err)


def download_files(args, api, source):
    """Download the translation files and save them as locales.

    Parameters
    ----------
    args: argparse.Namespace
        The arguments provided when running the script
    api: XTMCloudAPI
        Used for interacting with the project.
    source: FileSource
        Used to write the downloaded translation files locally.

    """
    try:
        raw_bytes = api.download_files(
            source.read_config().get(
                const.Config.XTM_SECTION, const.Config.PROJECT_OPTION,
            ),
        )
    except ConfigParser.NoOptionError, ConfigParser.NoSectionError:
        sys.exit(const.ErrorMessages.NO_PROJECT.format(source.get_path('')))
    except XTMCloudException as err:
        sys.exit(err)
    except str as err:
        sys.exit(err)

    try:
        with zipfile.ZipFile(BytesIO(raw_bytes)) as zf:
            zip_contents = zf.namelist()
            if len(zip_contents) == 0:
                sys.exit(
                    const.InfoMessages.NO_FILES_FOUND.format(args.project_id),
                )

            logging.info(const.InfoMessages.FILES_DOWNLOADED)
            locales_path = source.get_path('locales')
            default_locale = source.read_config().get(
                const.Config.MAIN_SECTION,
                const.Config.DEFAULT_LOCALE_OPTION,
            )
            valid_locales = utils.get_locales(locales_path, default_locale)
            utils.clear_files(locales_path, valid_locales)

            for name in zip_contents:
                path = utils.remote_to_local(name, locales_path, valid_locales)
                utils.write_to_file(zf.read(name), path)
                logging.info(const.InfoMessages.FILE_SAVED.format(
                    path,
                    zf.getinfo(name).file_size,
                ))
            logging.info(const.InfoMessages.GREETINGS)
    except zipfile.BadZipfile:
        sys.exit(const.ErrorMessages.NO_TARGET_FILES_FOUND)
    except IOError:
        sys.exit(const.ErrorMessages.COULD_NOT_SAVE_FILES)
