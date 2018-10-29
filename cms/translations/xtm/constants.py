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

"""Messages and other constants used by the translation script."""


class InfoMessages:
    PROJECT_NAME_CREATING = "Creating new project: '{0}'."
    PROJECT_CREATED = "Project created! The project ID is: '{0}'."
    GENERATING_TOKEN = "Generating token for '{0}' (userID: {1})."
    TOKEN_GENERATED = 'Token generated!: {}'
    TOKEN_SAVE_TO_ENV_VAR = ('To utilize the token, please copy-paste and '
                             'run the following command in your shell: '
                             '\n\n\t{}\n\n')
    NO_FILES_FOUND = 'No target files were found for project {}!'
    FILES_DOWNLOADED = 'Files downloaded! Now saving them to disc.'
    FILES_SAVED = 'Files successfully saved in {}!'
    EXTRACTING_STRINGS = 'Extracting page strings. This might take a while...'
    RESOLVING_LOCALES = 'Resolving locales...'
    ADDING_LANGUAGES = 'Adding the following languages to project {0}: {1}'
    UPLOADING_FILES = 'Uploading {0} files to the project! Please be patient.'
    CREATED_JOB = 'Created job {0} for {1}, with target language: {2}.'
    SAVED_PROJECT_ID = 'The project id was saved to settings.ini!'
    NO_JOBS_CREATED = 'No jobs were created for the current project!'
    FILES_UPLOADED = 'The files were successfully uploaded to XTM Cloud!'
    WAITING_FOR_PROJECT = ('Waiting for the project processing to finish. '
                           'This might take a while...')
    FILE_SAVED = 'Saved file {0} ({1}B).'
    GREETINGS = 'Bye! :D'


class ErrorMessages:
    NO_TARGET_LANG = 'Error: No target language was provided!'
    NO_TOKEN_PROVIDED = ('Error: No token found! Copy-paste and run the '
                         'following command in your shell to login and '
                         'generate the token: \n\n\t{}\n\n. Watch out: In '
                         'order for the token to be valid, re-run the script '
                         'in the same shell after generating it!')
    LOCALES_NOT_PRESENT = ('Error: The following languages are enabled in the '
                           'API, but not listed in locales: {0}! Please '
                           'remove them manually from project number {1} and '
                           'then re-run the script!')
    FILENAME_TOO_LONG = ('The filename is too long: {0}! XTM only supports '
                         'up to {1} characters!')
    CANT_RESOLVE_REMOTE_LANG = 'Cannot resolve remote locale: {0}'
    PROJECT_EXISTS = ('Error! There already exists an XTM project associated'
                      ' with this website (number {0})! If you want to '
                      'overwrite this, please delete the project id from '
                      'settings.ini and run this again.')
    NO_PROJECT = 'Error! No project configured for {}!'
    NO_TARGET_FILES_FOUND = ('Error: No target files were found in XTM! '
                             'Please generate them and then try again!')
    COULD_NOT_SAVE_FILES = ('Error: Could not save the downloaded files to '
                            'disk!')
    WORKFLOW_NAME_AND_ID_PROVIDED = ('Error: Provide only one of '
                                     '"--workflow-name" and "--workflow-id" '
                                     'at a time, not both.')
    NO_WORKFLOW_INFO = ('Error: No workflow information provided. Please '
                        'use one of "--workflow-id" or "--workflow-name" to '
                        'do that.')
    NO_WORKFLOW_FOR_NAME = ('Error: Could not find any workflow with the '
                            'name "{}"')


class WarningMessages:
    LOCALE_NOT_SUPPORTED = ('The following locale is not supported: "{0}". '
                            'Ignoring...')


class ProjectName:
    MAX_LENGTH = 150
    INVALID_CHARS = list('\\/:*?"<>|{}')
    NAME_WILDCARD = '_'


class Token:
    ENV_VAR = 'XTM_TOKEN'
    SAVE_COMMAND = "export {0}='{1}'"
    CREATION_CMD = 'python -m cms.bin.xtm_translations login'


class ArgumentsHelp:
    VERBOSE = 'Whether the script will log its work to stderr or not.'
    PROJECT_ID = ('The ID of the project we are working with. Will be '
                  'ignored if in "create" mode.')
    LOGIN = 'Mode used to generate and save an API token from username+pass.'
    PROJECT = ('Mode for handling projects: creation, files upload/ update/ '
               'download.')
    PROJECT_SOURCE_DIR = 'The source directory of the website.'
    PROJECT_DOWNLOAD = ('Download the translation files from a project and '
                        'save them to disk.')

    class ProjectCreate:
        MAIN = 'Sub-mode used to create a new project with XTM Cloud.'
        NAME = 'The name of the project will have once created.'
        DESC = 'TBD'
        CLIENT_ID = 'TBD'
        REF_ID = 'TBD'
        WORKFLOW_ID = 'TBD'
        SOURCE = 'The source language for this project. Default "en_US".'
        SAVE_ID = ('Whether to save the id of the project to settings.ini or '
                   'not. Default False.')
        WORKFLOW_NAME = 'The name of the workflow used in the project.'

    class ProjectUpload:
        MAIN = 'Sub-mode used to upload files to an XTM Cloud project.'
        NO_OVERWRITE = ('If set, the script will not overwrite the files '
                        'already present in the XTM environment.')


class Config:
    XTM_SECTION = 'XTM'
    PROJECT_OPTION = 'project_id'
    MAIN_SECTION = 'general'
    DEFAULT_LOCALE_OPTION = 'defaultlocale'


SUPPORTED_LOCALES = (
    'ab, aa_ET, ak, af_ZA, sq_AL, am_ET, am_ER, ar_AA, ar_AE,ar_BH, ar_DZ, '
    'ar_EG, ar_EH, ar_IQ, ar_JO, ar_KW, ar_LB, ar_LY, ar_MA, ar_MR, ar_OM, '
    'ar_PS, ar_QA, ar_SA, ar_SD, ar_SY, ar_TD, ar_TN, ar_YE, hy_AM, '
    'hy_AM_arevela, hy_AM_arevmda, as_IN, ast_ES, ay_BO, az_AZ_Cyrl, '
    'az_AZ_Latn, ba_RU, bal_IR, bh_IN, bi_VU, bs_BA_Cyrl, bs_BA_Latn, br_FR, '
    'bsk, my_MM, be_BY, cal, ca_ES, ceb, cha, ny_MW, zh_CN, zh_TW, zh_HK, '
    'zh_SG, chk, co_FR, hr_HR, hr_BA, cs_CZ, eu_ES, bn_IN, bn_BD, bg_BG, '
    'ca_AD, dnj, da_DK, prs_AF, dv_IN, mis, nl_NL, en_US, en_GB, en_142, '
    'en_CA, en_AU, en_NZ, en_ZA, en_CH, en_HK, en_IN, en_IE, en_SG, en_AE, '
    'en_DE, en_NL, en_AT, en_NT, en_CY, en_KE, en_BS, en_MY, en_PK, en_PH, eo,'
    ' et_EE, ee_GH, fo_FO, fj_FJ, fil_PH, fi_FI, nl_BE, fr_FR, fr_CA, fr_CH, '
    'fr_BE, fr_LU, fr_MA, fr_SN, fr_CM, fy, fu, fat, gl_ES, ka_GE, kar, de_DE,'
    ' de_AT, de_BE, de_CH, de_LU, de_NL, lb_LU, kl_GL, el_GR, el_CY, grc_GR, '
    'grn, gu_IN, ht_HT, cnh, ha_NG, he_IL, hi_IN, hil, hmn, hmn_US, hu_HU, '
    'haw, is_IS, ig, ilo, id_ID, ia, ie, iu, ium, ik, ga_IE, it_IT, it_CH, '
    'ja_JP, jv_ID, ks, kk_KZ, kg_CG, rw_RW, ky, rn, sw_KE, km_KH, kn_IN, '
    'kok_IN, tlh, ko_KR, kos, ku_TR, kmr, ckb, ku_IQ, lo_LA, la, lv_LV, ln_CG,'
    ' lt_LT, mfe_MU, mk_MK, mg_MG, ms_MY, ms_SG, ml_IN, mt_MT, mi_NZ, mr_IN, '
    'mah, mn_MN, sla_ME, mo_MD, na_NR, nv, nd_ZW, ne_NP, no_NO, nb_NO, nn_NO, '
    'nso_ZA, nus, oc_FR, or_IN, om_ET, ota, pau, ps, ps_PK, fa_IR, pon, pl_PL,'
    ' pt_PT, pt_BR, pt_MZ, pt_AO, pa_PA, pa_IN, pa_PK, qu_PE, qya, xr_MM, '
    'rm_CH, ro_RO, ro_MD, ru_RU, ru_AM, ru_AZ, ru_GE, ru_MD, ru_UA, sm_WS, sg,'
    ' sa_IN, sc_IT, gd_GB, st, tn_ZA, sr_YU, sr_RS_Cyrl, sr_ME_Cyrl, '
    'sr_ME_Latn, sr_RS_Latn, sn, sjn, sd_PK, si_LK, ss, sk_SK, sl_SI, so_SO, '
    'dsb_DE, hsb_DE, es_ES, es_AR, es_BO, es_CL, es_CO, es_CR, es_CU, es_DO, '
    'es_EC, es_SV, es_GT, es_HN, es_419, es_MX, es_NI, es_PA, es_PY, es_PE, '
    'es_PR, es_UY, es_US, es_VE, es_001, es_NT, swa, sw_SO, sw_TZ, sw_UG, '
    'sv_SE, sv_FI, apd_SD, apd_SD_Latn, sun, syr_TR, tl_PH, tg_TJ, ta_IN, '
    'ta_SG, ta_LK, tt_RU, te_IN, tet_ID, tet_TL, th_TH, bo, ti, to_TO, ts_ZA, '
    'tn_BW, tr_TR, tk_TM, tw, uk_UA, ur_IN, ur_PK, ug_CN, uz_UZ_Cyrl, '
    'uz_UZ_Latn, uz_AF, cy_GB, vi_VN, vo, wo, xh_ZA, xz_AF, yap, yi, yi_IL, '
    'yi_US, yo_NG, czt, zu_ZA, kun, lua, sco_GB, sco_IE, fr_CG, zh_YUE, lug, '
    'ogo, bbc, ksw, cfm, cmn, goyu, aii, cld, pdc'
).split(', ')


class FileNames:
    MAX_LENGTH = 256
    PATH_SEP_REP = '___'


UNDER_ANALYSIS_MESSAGE = ('403: {"reason":"Project is under analysis. '
                          'Please wait for analysis end."}')

MAX_WAIT_TIME = 10
