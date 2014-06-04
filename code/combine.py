#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import codecs
import logging
from optparse import OptionParser



DELIMITER = ";"



log = logging.getLogger('combine')

re_comment = re.compile("\s*#.*$")



def row_iter(path):
    with codecs.open(path, "r", "utf-8") as csv_file:
        for line in csv_file:
            line = re_comment.sub("", line)
            line = line.strip()
            if not line:
                continue
            parts = line.split(DELIMITER)
            parts = [part.strip() for part in parts]
            yield parts
        



def combine(path_list, complete=None, warn=None):
    data = {}

    if complete:
        names = {}
        complete_path = path_list.pop(0)
        for row in row_iter(complete_path):
            names[row[0]] = row[1]
            data[row[0]] = None

    for path in path_list:
        for row in row_iter(path):
            assert len(row) >= 2
            if complete and row[0] not in data:
                log.warning("# '%s' not in complete list." % row[0])
                continue
            data[row[0]] = row[1]

    if complete:
        fail = False
        for key in sorted(data.keys()):
            if data[key] is None:
                if warn:
                    log.warning("%s; " % key)
                    del data[key]
                else:
                    log.error("%s; ; %s" % (key, names[key]))
                    fail = True
        if fail:
            sys.exit(1)

    for key in sorted(data.keys()):
        sys.stdout.write((
            (DELIMITER + u" ").join((key, data[key])) + "\n"
        ).encode("utf-8"))



if __name__ == "__main__":
    log.addHandler(logging.StreamHandler())

    usage = """%prog CSV..."""

    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="count", dest="verbose",
                      help="Print verbose information for debugging.", default=0)
    parser.add_option("-q", "--quiet", action="count", dest="quiet",
                      help="Suppress warnings.", default=0)
    parser.add_option("-c", "--complete", action="store_true", dest="complete",
                      help="First file gives a complete list of IDs but no values. Raise an error (or optionally a warning) if subsequent file do not define values for all IDs.", default=None)
    parser.add_option("-w", "--warn", action="store_true", dest="warn",
                      help="Warn only on incomplete.", default=0)

    (options, args) = parser.parse_args()
    args = [arg.decode(sys.getfilesystemencoding()) for arg in args]

    log_level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG,)[
        max(0, min(3, 1 + options.verbose - options.quiet))]

    log.setLevel(log_level)

    if not len(args) > int(options.complete):
        parser.print_usage()
        sys.exit(1)

    combine(args, options.complete, options.warn)

