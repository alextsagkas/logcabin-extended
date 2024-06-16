"""Utilities to run tests and clean environment afterwards."""

import subprocess
import random

from localconfig import hosts
from common import Sandbox

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

        self.snapshotMinLogSize = 1024

        self.filename = None

        self.sandbox = Sandbox()
    
    def _print_attr(self):
        print "hosts: ", self.hosts
        print "servers: ", self.servers
        print "server_ids: ", self.server_ids
        print "cluster_uuid: ", self.cluster_uuid
        print "snapshotMinLogSize: ", self.snapshotMinLogSize
        print "filename: ", self.filename

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
    
    def initialize_cluster(self, server_command):
       print 'Initializing first server\'s log'
       print '--------------------------------'
       
       self.sandbox.rsh(
           self.hosts[0][0],
           '%s --bootstrap --config %s-%d.conf' %
           (self.filename, server_command, self.server_ids[0]),
           stderr=open('debug/bootstrap', 'w')
       ) 

    def cleanup(self):
        """Clean up the environment."""

        # Generated from TestFramework.create_config
        run_command('rm "%s-"*".conf"' % self.filename)
        run_command('rm -f debug/*')

        # Generated from LogCabin
        # run_command('rm -rf smoketeststorage/')
        # run_command('rm -rf "Storage/server"*"/"')
        # run_command('rm -rf "Server/server"*"/"')

        # Remove Sanbox instance
        del self.sandbox
        
if __name__ == '__main__':
    test1 = TestFramework()
    test1._print_attr()
    test1.create_configs("smoketest")
    test1.create_folders()
    test1.cleanup()
    