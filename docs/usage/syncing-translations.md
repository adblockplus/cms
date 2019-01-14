# Syncing translations #

Before syncing translations ensure the following:

- The `crowdin-project-name` setting has been set in the site's configuration.
- The `urllib3` Python module is installed.

Now to sync with Crowdin type the following:

    python -m cms.bin.translate www_directory crowdin_project_api_key [logging_level]

The script might take a while to run, it does the following things:

1. Requests information about your Crowdin project
2. Checks all local locales are supported by Crowdin and enabled for your project
3. Renders all pages in your default language and extracts all page strings
4. Creates any required directories in your Crowdin project
5. Uploads any new page strings and updates any existing page strings
6. Uploads any pre-existing translation files for any newly uploaded pages
7. Requests Crowdin generate a fresh translations export archive
8. Downloads the archive of translations and extracts it replacing all local
   translation files

Notes:

- You have to use the Crowdin project's API key, not your account API key
- You should probably enable "Skip untranslated strings" under your
  project settings.
- Translations are only _uploaded_ for new files. If you are syncing with
  Crowdin for the first time, and you have existing translation files pay
  attention to any warnings. If there are any problems it is recommended
  you re-create another fresh Crowdin project and try again. (Otherwise
  translations for the pages already uploaded could be lost!)
- If you are running the script from a cronjob or similar you will probably
  want to set the logging level to `ERROR` or similar

-----
Prev: [Generating static files](generate-static-files.md) | Up: [Home](../../README.md) | Next: [XTM Integration](xml-sync.md)
