"""Utilities to run tests and clean environment afterwards."""

import subprocess
import random

from localconfig import hosts
from common import Sandbox, sh

def run_shell_command(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print("Warning: Command failed:", e)

class TestFramework(object):
    
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
        run_shell_command('mkdir -p debug')

    def _initialize_first_server(self, server_command):
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
    
    def _reconfigure_cluster(self, reconf_opts=""):

        print '\nGrowing cluster'
        print '---------------'

        sh('build/Examples/Reconfigure %s %s set %s' %
           (
               "--cluster=%s" % ','.join([server_ip for server_ip in self.server_ips]),
               reconf_opts,
               ' '.join([server_ip for server_ip in self.server_ips])
            )
        )
    
    def initialize_cluster(self, server_command="build/LogCabin"):
        try:
            self._initialize_first_server(server_command)
            self._start_servers(server_command)
            self._reconfigure_cluster()
        except:
            self.cleanup()
    
    def execute_client_command(self, client_command):
        cluster = "--cluster=%s" % ','.join([server_ip for server_ip in self.server_ips])

        print '\nStarting %s %s on localhost' % (client_command, cluster)
        print '-' * 150

        try:
            client = self.sandbox.rsh(
                'localhost',
                '%s %s' % (client_command, cluster),
                stderr=open('debug/client_command_%d' % self.client_commands, 'w')
            )

            self.client_commands += 1
        except Exception as e:
            print "Clinet command error: ", e
            self.cleanup()

    def cleanup(self, debug=False):
        """Clean up the environment."""

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
    # test.execute_client_command("build/Examples/TreeOps write /dir2/file1")
    test.execute_client_command("build/Examples/TreeOps dump")

    test.cleanup()
    