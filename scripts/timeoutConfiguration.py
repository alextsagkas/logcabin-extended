"""
Script to configure election timeout between servers so that it respects the inherent
network properties of the system.
"""

from TestFramework import TestFramework

class TimeoutConfiguration(TestFramework):
        def __init__(self):
            super(TimeoutConfiguration, self).__init__()


def main():
    test = TimeoutConfiguration()
    test._print_attr()

    test.create_configs()
    test.create_folders()

    test.initialize_cluster()

    test.cleanup()

if __name__ == "__main__":
    main()