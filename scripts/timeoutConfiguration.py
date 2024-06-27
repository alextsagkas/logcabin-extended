"""
Script to configure election timeout between servers so that it respects the inherent
network properties of the system.
"""

from __future__ import print_function
import re

from TestFramework import TestFramework, run_shell_command

class TimeoutConfiguration(TestFramework):
    def __init__(self):
        super(TimeoutConfiguration, self).__init__()
        self.icmp_header = 8
        self.ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        self.ping_separator = r'~*'

    def ping_servers(
        self,
        number_of_pings=2,
        number_of_bytes=1024,
    ):
        """
        Ping all servers in the cluster from all servers in the cluster. The ping command is configured to exchange number_of_bytes data, whereas the number_of_pings pings are executed.

        Important: Before executing the pings the debug/ folder is cleared. The output of the ping commands is stored in files with the format: debug/client_command_<command_number>_out.
        """

        # Due to appending to the same files in debug/
        run_shell_command('rm -f debug/*')

        try:
            bytes_sent = number_of_bytes - self.icmp_header

            for from_server_id, from_server_ip in self.server_ids_ips:
                header = "\nPinging from server %s (%s)" % (from_server_id, from_server_ip)
                self._print_string(header)

                # Change stdout and stderr file whenever ssh-ing to different server
                self.client_commands += 1

                for _, to_server_ip in self.server_ids_ips:
                    command = "ping -c %s -s %s %s" % (
                        number_of_pings, number_of_bytes, to_server_ip
                    )

                    print(command)

                    self.sandbox.rsh(
                        '%s' % (from_server_ip),
                        command,
                        bg=False,
                        stdout=open('debug/client_command_%d_out' % self.client_commands, 'a'),
                        stderr=open('debug/client_command_%d' % self.client_commands, 'a')
                    )

                    with open('debug/client_command_%d_out' % self.client_commands, 'a') as f:
                        f.write('~' * 60 + '\n')
        except Exception as e:
            print("Client command error: ", e)
            self.cleanup()

    def ping_stats(self):
        """
        Store and return ping stats in a dictionary of the form:
        {
            'from_server_id_ip_1': {
                'to_server_id_ip_1': [ping_time_1, ping_time_2, ...],
                'to_server_id_ip_2': [ping_time_1, ping_time_2, ...],
                ...
            },
            'from_server_id_ip_2': {
                'to_server_id_ip_1': [ping_time_1, ping_time_2, ...],
                'to_server_id_ip_2': [ping_time_1, ping_time_2, ...],
                ...
            },
            ...
        }
        """

        ping_stats = {}

        for i, from_server_id_ip in enumerate(self.server_ids_ips, 1):

            ping_stats[from_server_id_ip] = {}

            for to_server_id_ip in self.server_ids_ips:

                ping_stats[from_server_id_ip][to_server_id_ip] = []

                with open('debug/client_command_%d_out' % i, 'r') as f:
                    for line in f:
                        # Skip to the next ping command
                        m = re.search(self.ping_separator, line)
                        if len(m.group(0)) != 0:
                            break

                        ping_stats[from_server_id_ip][to_server_id_ip].append(line)

        return ping_stats


def main():
    test = TimeoutConfiguration()
    test._print_attr()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster()

    test.cleanup()

if __name__ == "__main__":
    main()