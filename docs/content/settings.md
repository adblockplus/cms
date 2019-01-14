# Configuration (settings.ini) #

The following sections can be defined in `settings.ini`:

* `[general]`: following settings should be listed here:
  * `defaultlocale`: The fallback locale, to be used whenever no localized
    page/strings can be found for a locale.
  * `defaultpage`: the default page which is displayed by the server if the URL
    doesn't contain a page name. Note that while the test server will consider
    that setting automatically, the real server might need to be configured
    accordingly.
  * `crowdin-project-name`: The Crowdin project name, this must be set for if
    you intend to use the cms.bin.translate script to update the Crowdin
    translations.
* `[langnames]`: defines the language names correspoding to particular language
  codes.
* `[rtl]`: any language codes listed here are treated as right-to-left languages.
  The values of the settings are ignored.
* `[locale_overrides]`: every entry defines that a page should use a different
  locale file, not the one matching its name (to be used when multiple pages
  share localization data).

-----
Prev: [XTM Integration](../usage/xml-sync.md) | Up: [Home](../../README.md) | Next: [Custom Jinja2 global functions and variables (`globals`)](globals.md)
