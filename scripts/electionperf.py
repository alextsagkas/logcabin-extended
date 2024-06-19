#!/usr/bin/env python
# Copyright (c) 2012 Stanford University
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR(S) DISCLAIM ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL AUTHORS BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
This runs a LogCabin cluster and continually kills off the leader, timing how
long each leader election takes.
"""

from __future__ import print_function

import time
import sys
import re

from TestFramework import TestFramework 

class ElectionTest(TestFramework):
    def __init__(self):
        TestFramework.__init__(self)
    
    def _same(self, lst):
        """
        Check if all elements in a list are the same.
        """

        return len(set(lst)) == 1
    
    def _await_stable_leader(self, after_term=0):
        while True:
            server_beliefs = {}

            # Only the running servers are considered, whereas the self.server_ids_ips contains all
            # servers in the cluster.
            for server_id_ip, server_process in self.server_processes.items():
                server_beliefs[server_id_ip] = {'leader_id_ip': None,
                                                'term': None,
                                                'wake': None}
                b = server_beliefs[server_id_ip]

                for line in open('debug/server_%d' % server_id_ip[0]):

                    m = re.search('All hail leader (\d+) for term (\d+)', line)
                    if m is not None:
                        b['leader_id_ip'] = filter(
                                lambda server_id_ip: server_id_ip[0] == int(m.group(1)), 
                                self.server_ids_ips)[0]
                        b['term'] = int(m.group(2))
                        continue

                    m = re.search('Now leader for term (\d+)', line)
                    if m is not None:
                        b['leader_id_ip'] = server_id_ip
                        b['term'] = int(m.group(1))
                        continue

                    m = re.search('Running for election in term (\d+)', line)
                    if m is not None:
                        b['wake'] = int(m.group(1))

            terms = [b['term'] for b in server_beliefs.values()]
            leaders_ids_ips = [b['leader_id_ip'] for b in server_beliefs.values()]

            if self._same(terms) and terms[0] > after_term:
                assert self._same(leaders_ids_ips), server_beliefs

                return {'leader_id_ip': leaders_ids_ips[0],
                        'term': terms[0],
                        'num_woken': sum([1 for b in server_beliefs.values() if b['wake'] > after_term])}
            else:
                time.sleep(.25)
                self.sandbox.checkFailures()

    def election_performance(self, repeat=100):
        num_terms = []
        num_woken = []

        for i in range(repeat):
            old = self._await_stable_leader()
            print('Server %d is the leader in term %d' % (old['leader_id_ip'][0], old['term']))

            self._kill_server(old['leader_id_ip'])

            new = self._await_stable_leader(after_term=old['term'])
            print('Server %d is the leader in term %d' % (new['leader_id_ip'][0], new['term']))

            self.sandbox.checkFailures()

            num_terms.append(new['term'] - old['term'])
            print('Took %d terms to elect a new leader' % (new['term'] - old['term']))
            num_woken.append(new['num_woken'])
            print('%d servers woke up' % (new['num_woken']))

            self._start_server('build/LogCabin', old['leader_id_ip'])

        num_terms.sort()
        print('Num terms:', 
            file=sys.stderr)
        print('\n'.join(['%d: %d' % (i + 1, term) for (i, term) in enumerate(num_terms)]),
            file=sys.stderr)

        num_woken.sort()
        print('Num woken:',
            file=sys.stderr)
        print('\n'.join(['%d: %d' % (i + 1, n) for (i, n) in enumerate(num_woken)]),
            file=sys.stderr)

def main():
    test = ElectionTest()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster()

    test.election_performance(repeat=10)

    test.cleanup()

if __name__ == '__main__':
    main()