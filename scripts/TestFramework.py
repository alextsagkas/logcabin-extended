"""
Utilities to run tests and clean environment afterwards. An example of use is provided in the
main function.
"""

from __future__ import print_function

import subprocess
import random
import time
import sys
import re

from localconfig import hosts
from common import Sandbox, sh

def run_shell_command(command):
    """
    Run a shell command and print a warning if it fails.
    """

    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print("Warning: Command failed:", e)

class TestFramework(object):
    """
    Contains the functionality to run tests and clean up the environment afterwards.
    """
    
    def __init__(self):
        # List of tuples (server_id, server_ip) for each server in the cluster, generated from
        # common.hosts with 1-1 mapping.
        self.server_ids_ips = [(server_id, server_ip) for server_ip, _, server_id in hosts]

        alphabet = [chr(ord('a') + i) for i in range(26)]
        self.cluster_uuid = ''.join([random.choice(alphabet) for i in range(8)]) 

        self.snapshotMinLogSize = 1024

        self.filename = None

        self.sandbox = Sandbox()
        self.client_commands = 0

        # The running processes of the servers in the cluster. If a server is killed, the process
        # is removed from the dictionary. Otherwise, the process is kept in the dictionary from the
        # start of the server until the end of the test.
        self.server_processes = {}
    
    def _print_attr(self):
        print("server_ids_ips: ", self.server_ids_ips)
        print("cluster_uuid: ", self.cluster_uuid)
        print("snapshotMinLogSize: ", self.snapshotMinLogSize)
        print("filename: ", self.filename)
        print("sandbox: ", self.sandbox)
        print("client_commands: ", self.client_commands)
        print("server_processes: ", self.server_processes)

    def create_configs(self, filename="logcabin"):
        """ 
        Create configuration files for each server. 
        """

        self.filename = filename

        for server_id, server_ip in self.server_ids_ips:
            with open('%s-%d.conf' % (self.filename, server_id), 'w') as f:
                f.write('serverId = %d\n' % server_id)
                f.write('listenAddresses = %s\n' % server_ip)
                f.write('clusterUUID = %s\n' % self.cluster_uuid)
                f.write('snapshotMinLogSize = %s' % self.snapshotMinLogSize)
                f.write('\n\n')
                try:
                    f.write(open('smoketest.conf').read())
                except:
                    pass

    def create_folders(self):
        """ 
        Create necessary folders for the metadata of the test.
        """

        run_shell_command('mkdir -p debug')

    def _initialize_first_server(self, server_command):
        """ 
        Bootstrap the first server in the cluster. The bootrstap server is the first server in
        the cluster, so it acts as its leader until a new configuration is set.
        """

        print('\nInitializing first server\'s log')
        print('--------------------------------')
        
        server_id, server_ip = self.server_ids_ips[0]
        command = ('%s --bootstrap --config %s-%d.conf' %
                    (server_command, self.filename, server_id))

        print('Executing: %s on %s' % (command, server_ip))

        self.sandbox.rsh(
            server_ip,
            command,
            stderr=open('debug/bootstrap_server', 'w')
        ) 

    def _start_server(self, server_command, server_id_ip):
        """ 
        Start a server in the background process.
        """

        server_id, server_ip = server_id_ip
        command = ('%s --config %s-%d.conf' %
                    (server_command, self.filename, server_id))

        print('Executing: %s on %s' % (command, server_ip))
        print('-' * 66)

        self.server_processes[server_id_ip] = self.sandbox.rsh(
            server_ip,
            command,
            bg=True,
            stderr=open('debug/server_%d' % server_id, 'w')
        )
        self.sandbox.checkFailures()
        
    def _kill_server(self, server_id_ip):
        """ 
        Kill a server in the cluster.
        """

        print('Killing server %d at %s' % (server_id_ip[0], server_id_ip[1]))
        print('--------------------------------')

        server_process = self.server_processes[server_id_ip]

        del self.server_processes[server_id_ip]
        self.sandbox.kill(server_process)
    
    def _start_servers(self, server_command):
        """
        Starts the servers in the cluster in background processes. 
        """

        print('\nStarting servers')
        print('----------------')

        for server_id_ip in self.server_ids_ips:
            self._start_server(server_command, server_id_ip)
    
    def _reconfigure_cluster(self, reconf_opts):
        """
        Execute the reconfigure command to grow the cluster. 
        """

        print('\nGrowing cluster')
        print('---------------')

        sh('build/Examples/Reconfigure %s %s set %s' %
           (
               "--cluster=%s" % ','.join([server_ip for _, server_ip in self.server_ids_ips]),
               reconf_opts,
               ' '.join([server_ip for _, server_ip in self.server_ids_ips])
            )
        )
    
    def initialize_cluster(self, server_command="build/LogCabin", reconf_opts=""):
        """ 
        Initialize the cluster by bootstrapping the first server, starting the servers in the
        cluster and reconfiguring the cluster to contain all servers. 
        """

        try:
            self._initialize_first_server(server_command)
            self._start_servers(server_command)
            self._reconfigure_cluster(reconf_opts)
        except:
            self.cleanup()
    
    def execute_client_command(self, client_command, bg=False):
        """ 
        Executes a client command on the cluster. The client binary that is executed must provide
        a --cluster flag to specify the cluster to connect to. 
        """

        cluster = "--cluster=%s" % ','.join([server_ip for _, server_ip in self.server_ids_ips])

        print('\nStarting %s %s on localhost' % (client_command, cluster))
        print('-' * 150)

        try:
            self.client_commands += 1

            return self.sandbox.rsh(
                'localhost',
                '%s %s' % (client_command, cluster),
                bg=bg,
                stderr=open('debug/client_command_%d' % self.client_commands, 'w')
            )
        except Exception as e:
            print("Client command error: ", e)
            self.cleanup()
    
    def time_client_command(self, client_process, timeout_sec=10):
        start = time.time()

        while client_process.proc.returncode is None:
            self.sandbox.checkFailures()

            time.sleep(.1)

            if time.time() - start > timeout_sec:
                raise Exception('Warning: timeout exceeded!')
    
    def random_server_kill(self, server_command, timeout, killinterval, launchdelay):
        """ 
        Randomly kill a server in the cluster at a given interval and restart it after a given
        delay. The process is repeated until a timeout is met. The presence of errors is checked.
        """

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

    def cleanup(self, debug=False):
        """
        Clean up the environment: configuration files, debug files and storage folders. Also, 
        release the resources of the sandbox, concerning the remote processes.
        """

        # Generated from TestFramework.create_config
        run_shell_command('rm "%s-"*".conf"' % self.filename)
        if not debug:
            run_shell_command('rm -f debug/*')

        # Generated from LogCabin
        run_shell_command('rm -rf "Storage/server"*"/"')
        run_shell_command('rm -rf "Server/server"*"/"')

        # Release Ssandbox resources
        self.sandbox.__exit__(None, None, None)

        
if __name__ == '__main__':
    test = TestFramework()
    test._print_attr()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster()

    test.execute_client_command("build/Examples/TreeOps mkdir /dir1")
    test.execute_client_command("build/Examples/TreeOps mkdir /dir2")
    test.execute_client_command("build/Examples/TreeOps write /dir2/file1")
    test.execute_client_command("build/Examples/TreeOps dump")

    test.cleanup()
    