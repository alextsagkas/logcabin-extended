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
  --reconf=<opts>      Additional options to pass through to the Reconfigure
                       binary. [default: '']
"""

import random
import time

from docopt import docopt
from TestFramework import TestFramework

class FailoverTest(TestFramework):
    def __init__(self):
        TestFramework.__init__(self)
        # Hold metadata from each experiment.
        # E.g. start and end time, kill interval, launch delay
        self.experiment_metadata = {}
    
    def run_failovertest(self, writes):

        client_process = self.execute_client_command(
            client_executable = 'build/Examples/FailoverTest',
            conf = {
                "options": "--writes=%d" % (writes),
                "command": ""
            },
            bg = True
        )

        # This is placed after the start of the client command so as to increment the
        # self.client_commands counter first.
        self.experiment_metadata[self.client_commands] = {} # initialize
        self.experiment_metadata[self.client_commands]["start_time"] = time.time()
        self.experiment_metadata[self.client_commands]["writes"] = writes

        return client_process

    def random_server_kill(
        self,
        test_process,
        server_command,
        killinterval,
        launchdelay
    ):
        """ 
        Randomly kill a server in the cluster at a given interval and restart it after a given
        delay. The process is repeated until the failovertest exits. The presence of errors is
        checked.

        Important: The killinerval should be greater or equal to the launchdelay.
        """

        self.experiment_metadata[self.client_commands]["kill_interval"] = killinterval
        self.experiment_metadata[self.client_commands]["launch_delay"] = launchdelay

        start = time.time()
        lastkill = start
        tolaunch = [] # [(time to launch, server id)]

        while True:
            time.sleep(.1)

            self.sandbox.checkFailures()
            now = time.time()

            # Check if the failovertest exited
            if test_process.proc.poll() is not None:
                self.experiment_metadata[self.client_commands]["end_time"] = time.time()
                # Revive killed servers to start (probably) next test fresh
                for server_id_ip in self.server_ids_ips:
                    if server_id_ip not in self.server_processes.keys():
                        self._start_server(server_command, server_id_ip)
                # Exit infinite loop
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

    writes_array = [4, 6]

    killinervals = [2, 4]
    launchdelays = [1, 2]

    # Run the test
    test = FailoverTest()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster(server_command, reconf_opts)

    for writes in writes_array:
        for killinterval, launchdelay in zip(killinervals, launchdelays):
            print("\n===============================")
            print("killinterval: %d, launchdelay: %d" % (killinterval, launchdelay))
            print("===============================")

            process = test.run_failovertest(writes)
            test.random_server_kill(process, server_command, killinterval, launchdelay)

    test.cleanup()

if __name__ == '__main__':
    main()
