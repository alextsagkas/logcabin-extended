#!/usr/bin/env python

"""
This runs ReconfigureTest that constantly changes the configuration to a random
subset of all the servers participating in the initial one. This action is performed
for a specified number of tries

Usage:
  reconfiguretest.py [options]
  reconfiguretest.py (-h | --help)

Options:
  -h --help            Show this help message and exit
  --binary=<cmd>       Server binary to execute [default: build/LogCabin]
  --reconf=<opts>      Additional options to pass through to the Reconfigure
                       binary. [default: '']
  --tries=<num>        Number of times to reconfigure the cluster [default: 10]
"""

import random
import time

from docopt import docopt
from TestFramework import TestFramework, run_shell_command

class ReconfigureTest(TestFramework):
    def __init__(self):
        TestFramework.__init__(self)
        # Path to the csv file for the plot
        self.csv_file = "scripts/plot/csv/reconfigure.csv"
    
    def set_servers_num(self, servers_num):
        # Number of servers in the cluster
        self.server_ids_ips = self.server_ids_ips[:servers_num]

    def create_folders(self):
        TestFramework.create_folders(self)
        # Create the csv file for the plot
        with open("%s" % (self.csv_file), 'w') as f:
            # write the columns
            f.write('servers;time;tries\n')

    def cleanup(self, debug=False):
        TestFramework.cleanup(self, debug=debug)
        if not debug:
            # Remove the csv file
            run_shell_command("rm %s" % (self.csv_file))

    def membership_changes(self, tries):
        self.execute_client_command(
            client_executable = "build/Examples/ReconfigureTest",
            conf = {
                "options": "--tries=%d" % (tries),
                "command": ""
            }
        )

    def reconfigure_test(self, tries):
        start_time = time.time()
        self.membership_changes(tries)
        end_time = time.time()

        with open("%s" % (self.csv_file), 'a') as f:
            f.write('%d;%f;%d\n' % (
                len(self.server_ids_ips),
                end_time - start_time,
                tries)
            )

def run_test(
        server_command,
        reconf_opts,
        tries,
        debug = False
    ):
    test = ReconfigureTest()

    test.create_configs()
    test.create_folders()

    test._initialize_first_server(server_command)
    test._start_servers(server_command)

    for servers_num in range(5, 1, -1):
        print("=======================================")
        print("Running ReconfigureTest with servers: %d" % servers_num)
        print("=======================================")

        test.set_servers_num(servers_num)
        test._reconfigure_cluster(reconf_opts)
        test.reconfigure_test(tries)

        time.sleep(1)

    test.cleanup(debug=debug)


def main():
    # Parse command line arguments
    arguments = docopt(__doc__)

    server_command = arguments['--binary']

    reconf_opts = arguments['--reconf']
    if reconf_opts == "''":
        reconf_opts = ""

    tries = int(arguments['--tries'])

    # Run the test
    run_test(
        server_command = server_command,
        reconf_opts = reconf_opts,
        tries = tries,
        debug = True
    )

if __name__ == '__main__':
    main()
