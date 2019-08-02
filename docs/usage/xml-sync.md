# XTM Integration

The integration with the XTM API can be run using the following command:

    python -m cms.bin.xtm_translations [-h] [-v] {login,create,upload,download}


and it has four main operational modes:


## 1. XTM Login

This mode prompts the user for the login credentials and prompts
the API for the authentication token. This token should then be saved as an
environment variable to be used in the other modes. It can be run as follows:


    python -m cms.bin.xtm_translations [-h] [-v] login [-h]



## 2. Project Creation

In this mode, one can create an XTM project. It can be run as follows:


    python -m cms.bin.xtm_translations [-h] [-v] create [-h] --name NAME
                --desc DESC --client-id CLIENT_ID --ref-id REF_ID
                --workflow-id WORKFLOW_ID [--source-lang SOURCE_LANG]
                [--save-id] [source_dir]


where:
* --name* = The name of the project will have once created.
* *--desc** = The description you wish to add to the project.
* *--client-id** = The id of the **pre-configured** XTM client you want
associated with the project. Has to be an integer!
* *--ref-id** = The reference id you want associated with the XTM project.
* *--workflow-id** = The id of the **pre-configured** XTM workflow to be
associated with the project. Has to be an integer!
* *--source-lang* = The language of the source files. If not provided,
the script will use `en_US` by default.
* *--save-id* = Whether to save the id of the newly created project into
'settings.ini' or not.
* *source_dir* = The source directory of the website. If not specified, the
script would consider the current working directory as the source for the website.
It will be used to extract all the translation strings and create the files
to be uploaded on project creation. It will also be used to automatically
detect the target languages for this specific project.

**Note:** All arguments marked with * are **mandatory** and the script will
fail if not provided.

In order for this mode to work, it requires the XTM authentication token
to be saved in the `XTM_TOKEN` environment variable.


## 3. File Uploading

This mode can be used to upload new files for translation to an existing project.
It can be run as follows:


    python -m cms.bin.xtm_translations [-h] [-v] upload [-h] [--no-overwrite]
                [source_dir]


where:
* *--no-overwrite* = If this flag is set, then the script would **create new
files** in XTM, instead of overwriting the ones that were already there.
* *source_dir* = The source directory of the website. See above for the full
explanation.

If you wish to add a new target language to the project automatically,
simply create a corresponding directory in the website's `locales` directory
and the script will update the XTM project accordingly before uploading the
new files and will create jobs for the new languages as well.

In order for this mode to work, it requires two things to be present:
1. The XTM authentication token saved in the `XTM_TOKEN` environment variable.
2. The XTM project number present in `settings.ini`, under the `project_id`
option, in the `XTM` section.


## 4. Translation Files Downloading

This mode downloads the translation files from the XTM project and saves them
in the website's `locales` directory. It can be run as follows:

    python -m cms.bin.xtm_translations [-h] [-v] download [-h] [source_dir]


where `source_dir` is the source directory of the website. See above for full
explanation.

When run in this mode, the script will remove all the translation files that
were previously saved locally and then save the new ones in their place.

In order for this mode to work, three requirements need to be fulfilled:
1. The XTM authentication token saved in the `XTM_TOKEN` environment variable.
2. The XTM project number present in `settings.ini`, under the `project_id`
option, in the `XTM` section.
3. (At least one) translation file(s) to be present in XTM.


## Dependencies

On top of the Python standard library, this script requires the following
additional libraries to run correctly:

1. [Markdown](https://pypi.org/project/Markdown/)
2. [Jinja2](https://pypi.org/project/Jinja2/)
3. [Requests](https://pypi.org/project/requests/)

Prev: [Syncing translations](syncing-translations.md) | Up: [Home](../../README.md) | Next: [Configuration (`settings.ini`)](../content/settings.md)
