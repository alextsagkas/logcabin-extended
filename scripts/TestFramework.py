"""Utilities to run tests and clean environment afterwards."""

import subprocess
import random

from localconfig import hosts
from common import Sandbox, sh

def run_command(command):
    try:
        subprocess.check_call(command, shell=True)
    except subprocess.CalledProcessError as e:
        print("Warning: Command failed:", e)

class TestFramework(object):
    
    def __init__(self):
        self.hosts = hosts
        self.servers = [host for host, _, _ in self.hosts]
        self.server_ids = [server_id for _, _, server_id in self.hosts]

        alphabet = [chr(ord('a') + i) for i in range(26)]
        self.cluster_uuid = ''.join([random.choice(alphabet) for i in range(8)]) 
        self.cluster = "--cluster=%s" % ','.join([host for host in self.servers])

        self.snapshotMinLogSize = 1024

        self.filename = None

        self.sandbox = Sandbox()
        self.client_commands = 0
    
    def _print_attr(self):
        print "hosts: ", self.hosts
        print "servers: ", self.servers
        print "server_ids: ", self.server_ids
        print "cluster_uuid: ", self.cluster_uuid
        print "snapshotMinLogSize: ", self.snapshotMinLogSize
        print "filename: ", self.filename
        print "sandbox: ", self.sandbox

    def create_configs(self, filename="logcabin"):
        self.filename = filename

        for server_id in self.server_ids:
            with open('%s-%d.conf' % (self.filename, server_id), 'w') as f:
                f.write('serverId = %d\n' % server_id)
                f.write('listenAddresses = %s\n' % self.hosts[server_id - 1][0])
                f.write('clusterUUID = %s\n' % self.cluster_uuid)
                f.write('snapshotMinLogSize = %s' % self.snapshotMinLogSize)
                f.write('\n\n')
                try:
                    f.write(open('smoketest.conf').read())
                except:
                    pass

    def create_folders(self):
        run_command('rm -rf debug/*')
        run_command('mkdir -p debug')

    def _initialize_first_server(self, server_command):
       print '\nInitializing first server\'s log'
       print '--------------------------------'
       
       host = self.hosts[0]
       command = ('%s --bootstrap --config %s-%d.conf' %
                     (server_command, self.filename, self.server_ids[0]))

       print('Executing: %s on %s' % (command, host[0]))

       self.sandbox.rsh(
           host[0],
           command,
           stderr=open('debug/bootstrap', 'w')
       ) 
    
    def _start_servers(self, server_command):
        print '\nStarting servers'
        print '----------------'
        for server_id in self.server_ids:
            host = self.hosts[server_id - 1]
            command = ('%s --config %s-%d.conf' %
                       (server_command, self.filename, server_id))

            print('Executing: %s on %s' % (command, host[0]))
            self.sandbox.rsh(
                host[0], 
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
               self.cluster,
               reconf_opts,
               ' '.join([server for server in self.servers])
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
        print '\nStarting %s %s on localhost' % (client_command, self.cluster)
        print '-' * 150

        try:
            client = self.sandbox.rsh('localhost',
                             '%s %s' % (client_command, self.cluster),
                             stderr=open('debug/client_command_%d' % self.client_commands, 'w')
                            )

            self.client_commands += 1
        except Exception as e:
            print "Error: ", e
            self.cleanup()

    def cleanup(self, debug=False):
        """Clean up the environment."""

        # Generated from TestFramework.create_config
        run_command('rm "%s-"*".conf"' % self.filename)
        if not debug:
            run_command('rm -f debug/*')

        # Generated from LogCabin
        run_command('rm -rf "Storage/server"*"/"')
        run_command('rm -rf "Server/server"*"/"')

        # Release sandbox resources
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
    