import itertools

from TestFramework import TestFramework
from common import sh

class MultipleClients(TestFramework):
    def __init__(self):
        TestFramework.__init__(self)
        # All the running servers
        self.parent_server_ids_ips = self.server_ids_ips
        # Number of servers in the cluster
        self.server_ids_ips = self.parent_server_ids_ips

    def _start_servers(self, server_command):
        """
        Starts the servers in the cluster in background processes.
        """

        self._print_string('\nStarting servers')

        for server_id_ip in self.parent_server_ids_ips:
            self._start_server(server_command, server_id_ip)

    def _reconfigure_cluster(self, reconf_opts=""):
        """
        Execute the reconfigure command to grow the cluster. Take into account the running
        servers and the new ones.
        """

        self._print_string('\nGrowing cluster')

        # Important: The --cluster option must contain all the server (old and new)
        # or even non of the above (just a superset).
        sh('build/Examples/Reconfigure %s %s set %s' %
            (
                "--cluster=%s" % ','.join(
                    [server_ip for _, server_ip in self.parent_server_ids_ips]),
                    reconf_opts,
                ' '.join([server_ip for _, server_ip in self.server_ids_ips])
            )
        )

    def set_servers_num(
        self,
        servers_num,
    ):
        # Number of servers in the cluster
        self.server_ids_ips = self.parent_server_ids_ips[:servers_num]

    def execute_client_command_with_multiple_threads(
        self,
        threads=1,
        size=1024,
        writes=1000
    ):
        self._print_string('\nExecuting client command with %d threads' % threads)

        self.execute_client_command(
            client_executable="build/Examples/Benchmark",
            conf= {
                "options": "--threads=%s --size=%s --write=%s" % (threads, size, writes),
                "command": ""
            }
        )

def combinations(*arrays):
    """
    Return all possible combinations of the elements in the input (arbitrary number of) arrays.
    """
    return [list(x) for x in itertools.product(*arrays)]

def run_experiments(threads_array, sizes_array, writes_array, servers_num):
    arrays_combinations = combinations(threads_array, sizes_array, writes_array, servers_num)

    # Test preparation
    test = MultipleClients()

    test.create_configs()
    test.create_folders()

    # Intial configuration contains all the servers
    test.initialize_cluster()

    for threads, size, writes, servers in arrays_combinations:
        print("\n\n================================================")
        print("threads: %d, size: %d, writes: %d, servers: %d" % (threads, size, writes, servers))
        print("================================================\n\n")

        test.set_servers_num(servers)
        test._reconfigure_cluster()

        test.execute_client_command_with_multiple_threads(
            threads=threads,
            size=size,
            writes=writes
        )

    # Cleanup environment
    test.cleanup()

def main():
    # threads_array = [1, 10, 100]
    # sizes_array = [1024]
    # writes_array = [1000]
    # servers_num = [1, 2, 3, 4, 5]

    threads_array = [1, 10]
    sizes_array = [1024]
    writes_array = [1000]
    servers_num = [3]

    run_experiments(threads_array, sizes_array, writes_array, servers_num)

if __name__ == '__main__':
    main()