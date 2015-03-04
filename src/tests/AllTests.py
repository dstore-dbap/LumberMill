import unittest2 as unittest
import os

if __name__ == "__main__":
    test_dir = os.path.dirname(os.path.realpath(__file__))
    print("Running all tests in %s." % test_dir)
    os.chdir(test_dir)
    all_tests = unittest.TestLoader().discover('.', pattern='Test*.py')
    unittest.TextTestRunner().run(all_tests)
