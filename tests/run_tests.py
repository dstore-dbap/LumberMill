#!/usr/bin/env python

import unittest as unittest
import os
import re
import sys
import argparse
import coverage

pathname = os.path.abspath(__file__)
pathname = pathname[:pathname.rfind("/")]
sys.path.append(pathname[:pathname.rfind("/")])

"""
To run coverage and submit data to coveralls:
coverage run --source=lumbermill /usr/lib64/pypy-4.0/bin/nosetests --verbosity=3 Test*.py
coverage html -d coverage/
/usr/lib64/pypy-4.0/bin/coveralls
"""

def compileRegExPattern(pattern):
    regex = None
    try:
        regex = re.compile(include_test_filename_pattern)
    except:
        etype, evalue, etb = sys.exc_info()
        print("RegEx error for pattern %s. Exception: %s, Error: %s." % (include_test_filename_pattern, etype, evalue))
        exit()
    return regex


if __name__ == "__main__":
    test_dir = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser()
    parser.add_argument("--include", help="Regex pattern to include select tests. Default: Test*.py")
    parser.add_argument("--exclude", help="Regex pattern to exclude select tests. Default: None")
    args = parser.parse_args()
    include_test_filename_pattern = 'Test*.py' if not args.include else args.include

    """
    include_test_filename_pattern = '^Test.*\.py$' if not args.include else args.include
    include_test_filename_pattern = compileRegExPattern(include_test_filename_pattern)
    exclude_test_filename_pattern = None if not args.exclude else args.exclude
    if(exclude_test_filename_pattern):
        exclude_test_filename_pattern = compileRegExPattern(exclude_test_filename_pattern)
    test_suite = unittest.TestSuite()
    for (dirpath, dirnames, filenames) in os.walk(test_dir):
        for filename in filenames:
            if exclude_test_filename_pattern and exclude_test_filename_pattern.match(filename):
                continue
            if include_test_filename_pattern.match(filename):
                test_suite.addTest(filename)
    """
    os.chdir(test_dir)
    cov = coverage.coverage(config_file='../.coveragerc')
    cov.erase()
    cov.start()
    all_tests = unittest.TestLoader().discover('.', pattern=include_test_filename_pattern)
    unittest.TextTestRunner(verbosity=2).run(all_tests)
    cov.stop()
    #cov.annotate(directory='./coverage')
    cov.html_report(directory='./coverage')
    cov.report()
