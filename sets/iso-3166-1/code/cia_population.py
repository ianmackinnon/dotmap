#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import codecs
import logging
from optparse import OptionParser

from bs4 import BeautifulSoup



log = logging.getLogger('cia_codes')
re_whitespace = re.compile("\s+", re.U)
re_comment = re.compile("\s*#.*$")
DELIMITER = ";"



def row_iter(path, delimiter=DELIMITER):
    with codecs.open(path, "r", "utf-8") as csv_file:
        for line in csv_file:
            line = re_comment.sub("", line)
            line = line.strip()
            if not line:
                continue
            parts = line.split(delimiter)
            parts = [part.strip() for part in parts]
            yield parts
        



def text2csv(text_path, csv_path):

    names2iso2 = {}
    for row in row_iter(csv_path):
        names2iso2[row[3]] = row[0]

    for rank, name, population in row_iter(text_path, delimiter="\t"):
        iso2 = names2iso2.get(name, None)
        if iso2 is None:
            log.warning("# No ISO2 for %s" % name)
            continue

        population = int(population.replace(",", ""))
            
        row = [iso2, unicode(population), name]
        if row[0] in ("-", u'\xa0'):
            continue
        sys.stdout.write(("%s\n" % (DELIMITER + " ").join(row)).encode("utf-8"))



if __name__ == "__main__":
    log.addHandler(logging.StreamHandler())

    usage = """%prog TEXT CSV"""

    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="count", dest="verbose",
                      help="Print verbose information for debugging.", default=0)
    parser.add_option("-q", "--quiet", action="count", dest="quiet",
                      help="Suppress warnings.", default=0)

    (options, args) = parser.parse_args()

    log_level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG,)[
        max(0, min(3, 1 + options.verbose - options.quiet))]

    log.setLevel(log_level)

    if not len(args) == 2:
        parser.print_usage()
        sys.exit(1)

    text_path, csv_path = args

    text2csv(text_path, csv_path)

