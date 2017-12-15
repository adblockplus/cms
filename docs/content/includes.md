# Include files #

The following tag inserts an include file into the page (can be in a different
format):

    <? include foo ?>

Include files should be placed into the `includes` directory of the repository.
In the case above the contents of `includes/foo.md` or `includes/foo.tmpl` will
be inserted (whichever is present).