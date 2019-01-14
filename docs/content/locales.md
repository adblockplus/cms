# Localization files #

The language-specific data is stored in the `locales` directory. Each language
(identified by its locale code) is given a subdirectory here. The `.json` files
contain localizable strings using the following format:

    {
      "stringid": {
        "message": "Translated string",
        "description": "Optional string description"
      },
      ...
    }

Any other files are considered localizable files and will be available on the
server unchanged. This is useful for images for example: a language-dependent
image can be placed into the `locales/en` directory and a German version
of the same image into the `locales/de` directory. E.g. the file
`locales/en/foo.png` will be available on the server under the URL `/en/foo.png`.

-----
Prev: [Custom Jinja2 filters (`filters`)](filters.md) | Up: [Home](../../README.md) | Next: [Page layout templates (`templates`)](templates.md)
