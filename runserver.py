#!/usr/bin/env python
# This is a stub script loading test_server module, used by PyInstaller.

import runpy, sys, os

# Make sure hidden imports are found
import cms.bin.test_server
import markdown.extensions.attr_list

sys.argv[1:] = [os.curdir]
runpy.run_module("cms.bin.test_server", run_name="__main__")
