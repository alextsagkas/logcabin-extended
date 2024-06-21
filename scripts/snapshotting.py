"""
This tests the snapshotting capabilities and performance of LogCabin.

Usage:
  snapshotting.py [--client=<cmd>]... [options]
  snapshotting.py (-h | --help)

Options:
  -h --help                         Show this help message and exit
  --binary=<cmd>                    Server binary to execute [default: build/LogCabin]
  --reconf=<opts>                   Additional options to pass through to the Reconfigure
                                    binary. [default: '']
  --snapshotting=<bool>             Enable snapshotting [default: True]
  --timeout=<seconds>               Number of seconds to wait for client to complete before
                                    exiting with an ok [default: 10]
  --size=<bytes>                    Number of bytes written in each write [default: 1024]
  --writes=<num>                    Number of writes to perform [default: 1000]
"""

import re
import time

from docopt import docopt
from TestFramework import TestFramework

class SnapshotTest(TestFramework):
    def __init__(
        self, 
        snapshotMinLogSize = 67108864,
        snapshotRatio = 4,
        snapshotWatchdogMilliseconds = 10000
    ):
        TestFramework.__init__(
            self,
            snapshotMinLogSize,
            snapshotRatio,
            snapshotWatchdogMilliseconds,
        )

    def allowSnapshotting(self):
        for _, server_ip in self.server_ids_ips:
            self.execute_client_command(
                client_executable = "build/Client/ServerControl",
                conf = {
                    "options": "--timeout=10",
                    "command": "snapshot inhibit clear",
                    "server_ip": server_ip,
                },
                onCluster = False,
            )

    def disallowSnapshotting(self):
        for _, server_ip in self.server_ids_ips:
            self.execute_client_command(
                client_executable = "build/Client/ServerControl",
                conf = {
                    "options": "--timeout=10",
                    "command": "snapshot inhibit set",
                    "server_ip": server_ip,
                },
                onCluster = False,
            )

    def executeBenchmark(self, size, writes):
        self.execute_client_command(
            client_executable = "build/Examples/Benchmark",
            conf = {
                "options": "--size=%s --writes=%s" % (size, writes),
                "command": "",
            }
        )

    def dumpStats(self):
        for _, server_ip in self.server_ids_ips:
            self.execute_client_command(
                client_executable = "build/Client/ServerControl",
                conf = {
                    "options": "--timeout=10",
                    "command": "stats dump",
                    "server_ip": server_ip,
                },
                onCluster = False,
            )

    def printStats(self):
        for server_id, _ in self.server_ids_ips:
            self._print_string("\nServer %d stats" % server_id)

            for line in open('debug/server_%d' % server_id):
                m = re.search('num_snapshots_attempted: (\d+)', line)
                if m is not None:
                    print "Snapshots attempted: %s" % m.group(1)

                m = re.search('num_snapshots_failed: (\d+)', line)
                if m is not None:
                    print "Snapshots failed: %s" % m.group(1)
                
                m = re.search('num_write_attempted: (\d+)', line)
                if m is not None:
                    print "Write attempted: %s" % m.group(1)

                m = re.search('num_write_success: (\d+)', line)
                if m is not None:
                    print "Write succeded: %s" % m.group(1)


def main():
    # Parse command line arguments
    arguments = docopt(__doc__)

    server_command = arguments['--binary']

    reconf_opts = arguments['--reconf']
    if reconf_opts == "''":
        reconf_opts = ""

    snapshotting = True if arguments['--snapshotting'] == 'True' else False

    timeout = int(arguments['--timeout'])
    size = int(arguments['--size'])
    writes = int(arguments['--writes'])

    # Run the test
    snapshotTest = SnapshotTest(
        snapshotMinLogSize = 1024000,
        snapshotRatio = 4,
        snapshotWatchdogMilliseconds = 1000
    )

    snapshotTest._print_attr()

    snapshotTest.create_configs()
    snapshotTest.create_folders()

    snapshotTest.initialize_cluster(server_command, reconf_opts)

    if snapshotting:
        snapshotTest.allowSnapshotting()
    else:
        snapshotTest.disallowSnapshotting()

    snapshotTest.executeBenchmark(size, writes)

    snapshotTest.dumpStats()
    snapshotTest.printStats()

    snapshotTest.cleanup()

if __name__ == "__main__":
    main()