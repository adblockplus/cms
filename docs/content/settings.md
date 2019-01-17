# Configuration (settings.ini) #

The following sections can be defined in `settings.ini`:

* `[general]`: The following settings should be listed here:
  * `defaultlocale`: The fallback locale, to be used whenever no localized
    page/strings can be found for a locale.
  * `defaultpage`: The default page which is displayed by the server if the URL
    doesn't contain a page name. Note that while the test server will consider
    that setting automatically, the real server might need to be configured
    accordingly.
  * `crowdin-project-name`: The Crowdin project name, this must be set if
    you intend to use the cms.bin.translate script to update the Crowdin
    translations.
  * `siteurl`: The base URL where pages will be served from.
* `[langnames]`: Defines the language names correspoding to particular language
  codes.
* `[rtl]`: Any language codes listed here are treated as right-to-left languages.
  The values of the settings are ignored.
* `[locale_overrides]`: Every entry defines that a page should use a different
  locale file, not the one matching its name (to be used when multiple pages
  share localization data).
* `[paths]`: Configure where things are located on the filesystem:
  * `additional-paths`: One or more additional website root directories (paths
    should be relative to the root directory of this website). Pages, templates,
    translations, etc. from those websites will be added to this one. This is
    useful for sharing common resources between multiple websites.

Prev: [XTM Integration](../usage/xml-sync.md) | Up: [Home](../../README.md) | Next: [Custom Jinja2 global functions and variables (`globals`)](globals.md)
