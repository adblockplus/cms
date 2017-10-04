# This file is part of the Adblock Plus web scripts,
# Copyright (C) 2006-present eyeo GmbH
#
# Adblock Plus is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# Adblock Plus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adblock Plus.  If not, see <http://www.gnu.org/licenses/>.

import contextlib
import os
import signal
import subprocess
import time


def get_dir_contents(path):
    # TODO: This function is duplicated in test_page_outputs.py.
    dirdata = {}
    for dirpath, dirnames, filenames in os.walk(path):
        for output_file in filenames:
            filepath = os.path.join(dirpath, output_file)
            with open(filepath) as f:
                locale = os.path.split(os.path.split(filepath)[0])[1]
                dirdata[os.path.join(locale, output_file)] = f.read().strip()
    return dirdata


@contextlib.contextmanager
def run_test_server(site_path):
    """Run test server, yield its URL. Terminate server on next iteration.

    This function is intended be used in a pytest fixture.
    """
    args = ['python', 'runserver.py', site_path]
    # Werkzeug is a dependency of flask which we are using for the mock api
    # however there is an issue with Werkzeug that prevents it from properly
    # handling the SIGTERM sent by p.kill() or terminate()
    # Issue: https://github.com/pallets/werkzeug/issues/58
    p = subprocess.Popen(args, stdout=subprocess.PIPE, preexec_fn=os.setsid)
    time.sleep(0.5)
    yield 'http://localhost:5000/'
    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
