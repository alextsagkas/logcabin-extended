#!/usr/bin/env python

"""
This runs ReconfigureTest that constantly changes the configuration to a random
subset of all the servers participating in the initial one.

Usage:
  reconfiguretest.py [options]
  reconfiguretest.py (-h | --help)

Options:
  -h --help            Show this help message and exit
  --binary=<cmd>       Server binary to execute [default: build/LogCabin]
  --reconf=<opts>      Additional options to pass through to the Reconfigure
                       binary. [default: '']
  --timeout=<seconds>  Number of seconds to wait for client to complete before
                       exiting with an ok [default: 20]
"""

import random
import time

from docopt import docopt
from TestFramework import TestFramework

class ReconfigureTest(TestFramework):
    def __init__(self):
        TestFramework.__init__(self)
    
    def check_timeout(self, client_process, timeout):
        start = time.time()
        while client_process.proc.returncode is None:

            time.sleep(.1)
            
            self.sandbox.checkFailures()

            if time.time() - start > timeout:
                client_process.proc.kill()
                time.sleep(0.5)
                print("Success: Timeout met with no errors!")
                break


def main():
    # Parse command line arguments
    arguments = docopt(__doc__)

    server_command = arguments['--binary']

    reconf_opts = arguments['--reconf']
    if reconf_opts == "''":
        reconf_opts = ""

    timeout = int(arguments['--timeout'])

    # Run the test
    test = ReconfigureTest()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster(server_command, reconf_opts)

    time.sleep(1)

    client_process = test.execute_client_command("build/Examples/ReconfigureTest", bg=True)
    test.check_timeout(client_process, timeout)

    test.cleanup()

if __name__ == '__main__':
    main()
