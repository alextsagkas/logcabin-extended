#!/usr/bin/env python
# Copyright (c) 2012-2014 Stanford University
# Copyright (c) 2014-2015 Diego Ongaro
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR(S) DISCLAIM ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL AUTHORS BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


"""
The incentive of this test is to check the optimization of reducing the number 
AppendEntries RPCs a leader sends to follower so as to make their logs consistent.

Usage:
  reduceAppendEntries.py [options]
  reduceAppendEntries.py (-h | --help)

Options:
  -h --help            Show this help message and exit
  --binary=<cmd>       Server binary to execute [default: build/LogCabin]
  --reconf=<opts>      Additional options to pass through to the Reconfigure
                       binary. [default: '']
"""

import random
import time

from docopt import docopt
from TestFramework import TestFramework

class reduceAppendEntries(TestFramework):
    def __init__(self):
        TestFramework.__init__(self)
    
    def random_server_kill(self, server_command, timeout, killinterval, launchdelay):

        start = time.time()
        lastkill = start
        tolaunch = [] # [(time to launch, server id)]

        while True:
            time.sleep(.1)

            self.sandbox.checkFailures()
            now = time.time()

            # Check if the timeout has been met
            if now - start > timeout:
                print('\nSuccess: Timeout met with no errors!')
                break

            # Check if the kill interval has been met
            if now - lastkill > killinterval:
                server_id_ip = random.choice(self.server_processes.keys())

                self._kill_server(server_id_ip)

                lastkill = now
                tolaunch.append((now + launchdelay, server_id_ip))

            # Check if lanchdelay has been met and there are servers to launch
            while tolaunch and now > tolaunch[0][0]:
                server_id_ip = tolaunch.pop(0)[1]
                self._start_server(server_command, server_id_ip)

def main():
    # Parse command line arguments
    arguments = docopt(__doc__)

    server_command = arguments['--binary']

    reconf_opts = arguments['--reconf']
    if reconf_opts == "''":
        reconf_opts = ""

    # Run the test
    test = reduceAppendEntries()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster(server_command, reconf_opts)

    test.execute_client_command(
        client_executable = "build/Examples/TreeOps",
        conf = {
            "options": "",
            "command": "mkdir /dir1/"
        }
    )

    test.execute_client_command(
        client_executable = "build/Examples/TreeOps",
        conf = {
            "options": "",
            "command": "mkdir /dir2/"
        }
    )

    test.execute_client_command(
        client_executable = "build/Examples/TreeOps",
        conf = {
            "options": "",
            "command": "dump"
        }
    )

    test.cleanup()

if __name__ == '__main__':
    main()
