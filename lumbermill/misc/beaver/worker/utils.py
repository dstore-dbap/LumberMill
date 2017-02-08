"""
Copyright (c) 2012 Jose Diaz-Gonzalez

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import itertools
import platform
import glob2
import re

IS_GZIPPED_FILE = re.compile('.gz$')
REOPEN_FILES = 'linux' not in platform.platform().lower()
ENCODINGS = [
    'windows-1252',
    'iso-8859-1',
    'iso-8859-2',
]

cached_regices = {}

def eglob(path, exclude=None):
    """Like glob.glob, but supports "/path/**/{a,b,c}.txt" lookup"""
    fi = itertools.chain.from_iterable
    paths = list(fi(glob2.iglob(d) for d in expand_paths(path)))
    if exclude:
        cached_regex = cached_regices.get(exclude, None)
        if not cached_regex:
            cached_regex = cached_regices[exclude] = re.compile(exclude)
        paths = [x for x in paths if not cached_regex.search(x)]

    return paths


def multiline_merge(lines, current_event, re_after, re_before):
    """ Merge multi-line events based.
        Some event (like Python trackback or Java stracktrace) spawn
        on multiple line. This method will merge them using two
        regular expression: regex_after and regex_before.
        If a line match re_after, it will be merged with next line.
        If a line match re_before, it will be merged with previous line.
        This function return a list of complet event. Note that because
        we don't know if an event is complet before another new event
        start, the last event will not be returned but stored in
        current_event. You should pass the same current_event to
        successive call to multiline_merge. current_event is a list
        of lines whose belong to the same event.
    """
    events = []
    for line in lines:
        if re_before and re_before.match(line):
            current_event.append(line)
        elif re_after and current_event and re_after.match(current_event[-1]):
            current_event.append(line)
        else:
            if current_event:
                events.append('\n'.join(current_event))
            current_event.clear()
            current_event.append(line)

    return events