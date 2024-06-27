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
        self.time_pattern = r'time=(\d+\.\d+) ms'
        # Exponential Weighted Moving Average (EWMA) parameters
        self.alpha = 0.125
        self.beta = 0.25
        # Window for timetout calculation
        self.timeout_window = 4

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

            with open('debug/client_command_%d_out' % i, 'r') as f:

                for to_server_id_ip in self.server_ids_ips:

                    ping_stats[from_server_id_ip][to_server_id_ip] = []

                    for line in f:
                        # Skip to the next ping command
                        m = re.search(self.ping_separator, line)
                        if len(m.group(0)) != 0:
                            break

                        # Extract the time from the ping command
                        m = re.search(self.time_pattern, line)
                        if  (m is not None and
                            len(m.group(0)) != 0):
                            ping_stats[from_server_id_ip][to_server_id_ip].append(float(m.group(1)))

        return ping_stats

    def estimate_rtt(
        self,
        ping_stats,
        old_ewma = None
    ):
        """
        Calculates the estimated RTT of the ping times between servers. It uses the Exponential
        Weighted Moving Average (EWMA) method. Also, it calculates the estimated deviation of the
        RTT. If old_ewma is provided, the new EWMA is calculated based on the old EWMA.

        The returned dictionary (as the one used, optionally, for inputs) has the form:
            {
                "average": estimated_rtt,
                "deviation": estimated_deviation
            }
        The times are in milliseconds.
        """

        # Initialize the estimation
        if old_ewma is None:
            estimation = {
                "average": 10,
                "deviation": 10,
            }
        else :
            estimation = {
                "average": old_ewma["average"],
                "deviation": old_ewma["deviation"],
            }

        for from_server, to_server_stats in ping_stats.items():
            for to_server, ping_times in to_server_stats.items():
                for ping_time in ping_times:
                    # Calculate the new average
                    estimation["average"] = (
                        (1 - self.alpha) * estimation["average"] +
                        self.alpha * ping_time
                    )

                    # Calculate the new deviation
                    estimation["deviation"] = (
                        (1 - self.beta) * estimation["deviation"] +
                        self.beta * abs(ping_time - estimation["average"])
                    )

        return estimation

    def caclulate_timeout(self, estimation):
        return estimation["average"] + self.timeout_window * estimation["deviation"]



def main():
    test = TimeoutConfiguration()
    test._print_attr()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster()

    test.cleanup()

if __name__ == "__main__":
    main()