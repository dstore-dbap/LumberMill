import unittest2 as unittest
import os
import argparse

if __name__ == "__main__":
    test_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", help="Matching pattern to select tests. Default: Test*.py")
    args = parser.parse_args()
    test_filename_pattern = 'Test*.py' if not args.pattern else args.pattern
    os.chdir(test_dir)
    all_tests = unittest.TestLoader().discover('.', pattern=test_filename_pattern)
    unittest.TextTestRunner().run(all_tests)
