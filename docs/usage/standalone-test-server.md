# Generating the standalone test server #

The standalone test server is a single binary, without any further dependencies.
It can be copied to another system and will no longer require Python or any of
its modules. In order to generate the standalone test server you need all the
prerequisites required to run the test server and
[PyInstaller](https://github.com/pyinstaller/pyinstaller/wiki). PyInstaller can
be installed by running `easy_install pyinstaller`.

Run the following command from the directory of the `cms` repository:

    pyinstaller runserver.spec

If successful, this will put the standalone test server into the `dist`
directory.

-----
Prev: [Running the test server](test-server.md) | Up: [Home](../../README.md) | Next: [Generating static files](generate-static-files.md)
