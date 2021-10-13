# CMS

Multi-language static content management system used by Adblock Plus websites.

This project has been restarted as [eyeo/websites/liven](https://gitlab.com/eyeo/websites/liven).

[eyeo/websites/liven](https://gitlab.com/eyeo/websites/liven) is not in use in production yet.

## Dependencies

- Python 2.7
- pip for Python 2
- pip modules in requirements.txt (`pip install -r requirements.txt`)

## Usage

- Testing/development server `python path/to/cms/runserver.py path/to/website`
- Production build `python path/to/cms/generate_static_pages.py path/to/website path/to/output`

## Further reading

Caution: Translations are no longer being synced via crowdin, xtm, or csv in production.

- How to use
    - [Running the test server](docs/usage/test-server.md)
    - [Generating the standalone test server](docs/usage/standalone-test-server.md)
    - [Generating static files](docs/usage/generate-static-files.md)
    - [Syncing translations](docs/usage/syncing-translations.md)
    - [XTM Integration](docs/usage/xml-sync.md)
- Content structure
    - [Configuration (`settings.ini`)](docs/content/settings.md)
    - [Custom Jinja2 global functions and variables (`globals`)](docs/content/globals.md)
    - [Custom Jinja2 filters (`filters`)](docs/content/filters.md)
    - [Localization files (`locales`)](docs/content/locales.md)
    - [Page layout templates (`templates`)](docs/content/templates.md)
    - [Various include files (`includes`)](docs/content/includes.md)
    - [User-visible pages (`pages`)](docs/content/pages.md)
    - [Static content (`static`)](docs/content/static.md)
- API
    - [Variables](docs/api/variables.md)
    - [Custom filters](docs/api/filters.md)
    - [Global functions](docs/api/functions.md)
