import re
import sys
from optparse import OptionParser 

parser = OptionParser()
parser.add_option("-r", "--regex", dest="regex")
parser.add_option("-s", "--string", dest="string")
parser.add_option("-f", "--file", dest="file")

(options, args) = parser.parse_args()
if options.file:
    with open(options.file) as f:
        string = f.readlines()
    test_string = string[0]
else:
    test_string = options.string
try:
    regex_comp = re.compile(options.regex)
    matches = regex_comp.search(test_string)
    if not matches:
        print "Regex does not match."
        sys.exit(255)
    print "Regex matches:"
    print "%s" % matches.groupdict()
except Exception, e:
    print "Could not test regex. Exception: %s, Error: %s" % (Exception ,e)