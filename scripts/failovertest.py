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
This runs some basic tests against a LogCabin cluster while periodically
killing servers.

Usage:
  failovertest.py [--client=<cmd>]... [options]
  failovertest.py (-h | --help)

Options:
  -h --help            Show this help message and exit
  --binary=<cmd>       Server binary to execute [default: build/LogCabin]
  --client=<cmd>       Client binary to execute
                       [default: 'build/Examples/FailoverTest']
  --reconf=<opts>      Additional options to pass through to the Reconfigure
                       binary. [default: '']
  --servers=<num>      Number of servers [default: 5]
  --timeout=<seconds>  Number of seconds to wait for client to complete before
                       exiting with an ok [default: 20]
  --killinterval=<seconds>  Number of seconds to wait between killing servers
                            [default: 5]
  --launchdelay=<seconds>  Number of seconds to wait before restarting server
                           [default: 0]
"""

from docopt import docopt
import os
import random
import subprocess
import time

from TestFramework import TestFramework

def main():
    # Parse command line arguments
    arguments = docopt(__doc__)

    server_command = arguments['--binary']
    client_commands = arguments['--client']

    reconf_opts = arguments['--reconf']
    if reconf_opts == "''":
        reconf_opts = ""

    timeout = int(arguments['--timeout'])
    killinterval = int(arguments['--killinterval'])
    launchdelay = int(arguments['--launchdelay'])

    # Run the test
    test = TestFramework()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster(server_command, reconf_opts)

    for client_command in client_commands:
        test.execute_client_command(client_command, bg=True)

    test.random_server_kill(server_command, timeout, killinterval, launchdelay)

    test.cleanup()

if __name__ == '__main__':
    main()
