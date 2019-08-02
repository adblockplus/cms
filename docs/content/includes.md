# Include files #

The following tag inserts an include file into the page (can be in a different
format):

    <? include foo ?>

Include files should be placed into the `includes` directory of the repository.
In the case above the contents of `includes/foo.md` or `includes/foo.tmpl` will
be inserted (whichever is present).

Also, the metadata variables from the include file are merged with the page metadata
(with the include file's metadata having priority). This means that a include file
is capable of things like overriding a page's default template, or title.

-----
Prev: [Page layout templates (`templates`)](templates.md) | Up: [Home](../../README.md) | Next: [User-visible pages (`pages`)](pages.md)
