#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import logging
from optparse import OptionParser

from bs4 import BeautifulSoup



log = logging.getLogger('cia_codes')
re_whitespace = re.compile("\s+", re.U)
delimiter = ";"



def html2csv(html_path):
    with open(html_path) as html_file:
        soup = BeautifulSoup(html_file)
        appendix = soup.find("ul", {"id": "GetAppendix_D"})

        for table in appendix.find_all("table"):
            table_iso = table.find("table")
            if not table_iso:
                continue

            name = table.find("a").text
            if not name:
                log.error("No name.")
                sys.exit(1)
            row = [td.text for td in table_iso.find_all("td")] + [name]
            if row[0] in ("-", u'\xa0'):
                continue
            sys.stdout.write(("%s\n" % (delimiter + " ").join(row)).encode("utf-8"))



if __name__ == "__main__":
    log.addHandler(logging.StreamHandler())

    usage = """%prog HTML"""

    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="count", dest="verbose",
                      help="Print verbose information for debugging.", default=0)
    parser.add_option("-q", "--quiet", action="count", dest="quiet",
                      help="Suppress warnings.", default=0)

    (options, args) = parser.parse_args()

    log_level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG,)[
        max(0, min(3, 1 + options.verbose - options.quiet))]

    log.setLevel(log_level)

    if not len(args) == 1:
        parser.print_usage()
        sys.exit(1)

    html_path = args[0]

    html2csv(html_path)

