"""
Utilities to run tests and clean environment afterwards. An example of use is provided in the
main function.
"""

import subprocess
import random
import time

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
        self.server_ips = [host for host, _, _ in hosts]
        self.server_ids = [server_id for _, _, server_id in hosts]

        alphabet = [chr(ord('a') + i) for i in range(26)]
        self.cluster_uuid = ''.join([random.choice(alphabet) for i in range(8)]) 

        self.snapshotMinLogSize = 1024

        self.filename = None

        self.sandbox = Sandbox()
        self.client_commands = 0
    
    def _print_attr(self):
        print "server_ips: ", self.server_ips
        print "server_ids: ", self.server_ids
        print "cluster_uuid: ", self.cluster_uuid
        print "snapshotMinLogSize: ", self.snapshotMinLogSize
        print "filename: ", self.filename
        print "sandbox: ", self.sandbox
        print "client_commands: ", self.client_commands

    def create_configs(self, filename="logcabin"):
        """ 
        Create configuration files for each server. 
        """

        self.filename = filename

        for server_id, server_ip in zip(self.server_ids, self.server_ips):
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

        print '\nInitializing first server\'s log'
        print '--------------------------------'
        
        server_ip = self.server_ips[0]
        command = ('%s --bootstrap --config %s-%d.conf' %
                    (server_command, self.filename, self.server_ids[0]))

        print('Executing: %s on %s' % (command, server_ip))

        self.sandbox.rsh(
            server_ip,
            command,
            stderr=open('debug/bootstrap_server', 'w')
        ) 
    
    def _start_servers(self, server_command):
        """
        Starts the servers in the cluster in background processes. 
        """

        print '\nStarting servers'
        print '----------------'

        for server_id, server_ip in zip(self.server_ids, self.server_ips):
            command = ('%s --config %s-%d.conf' %
                       (server_command, self.filename, server_id))

            print('Executing: %s on %s' % (command, server_ip))

            self.sandbox.rsh(
                server_ip, 
                command, 
                bg=True,
                stderr=open('debug/server_%d' % server_id, 'w')
            )
            self.sandbox.checkFailures()
    
    def _reconfigure_cluster(self, reconf_opts):
        """
        Execute the reconfigure command to grow the cluster. 
        """

        print '\nGrowing cluster'
        print '---------------'

        sh('build/Examples/Reconfigure %s %s set %s' %
           (
               "--cluster=%s" % ','.join([server_ip for server_ip in self.server_ips]),
               reconf_opts,
               ' '.join([server_ip for server_ip in self.server_ips])
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
    
    def execute_client_command(self, client_command):
        """ 
        Executes a client command on the cluster. The client binary that is executed must provide
        a --cluster flag to specify the cluster to connect to. 
        """

        cluster = "--cluster=%s" % ','.join([server_ip for server_ip in self.server_ips])

        print '\nStarting %s %s on localhost' % (client_command, cluster)
        print '-' * 150

        try:
            self.client_commands += 1

            return self.sandbox.rsh(
                'localhost',
                '%s %s' % (client_command, cluster),
                bg=True,
                stderr=open('debug/client_command_%d' % self.client_commands, 'w')
            )
        except Exception as e:
            print "Client command error: ", e
            self.cleanup()
    
    def time_client_command(self, client_process, timeout_sec=10):
        start = time.time()

        while client_process.proc.returncode is None:
            self.sandbox.checkFailures()

            time.sleep(.1)

            if time.time() - start > timeout_sec:
                raise Exception('Warning: timeout exceeded!')

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
    