from TestFramework import TestFramework

def main():
    test = TestFramework()

    test._print_attr()

    test.create_configs()

    test.cleanup()

if __name__ == "__main__":
    main()