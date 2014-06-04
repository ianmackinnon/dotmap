#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from optparse import OptionParser
from collections import defaultdict

import shapefile

from geometry import Geometry



DELIMITER = u";"



log = logging.getLogger('world2group')



def world2group(shp_path):
    log.info(shp_path)
    sf = shapefile.Reader(shp_path)

    field_names = [field[0] for field in sf.fields[1:]]

    for record in sf.records():
        for i, value in enumerate(record):
            if isinstance(value, str):
                record[i] = value.decode("utf-8")
         
        country = dict(zip(field_names, record))
        if country["ISO_A2"] == "-99":
            continue

        group = country["REGION_UN"]
        
        if country["SUBREGION"] == "Caribbean":
            group = "Caribbean"

        if group == "Asia" and country["REGION_WB"] == "Middle East & North Africa":
            group = "Middle East"

        if group in ("Europe", "Asia"):
            group = "Eurasia"

        if group == "Seven seas (open ocean)":
            continue

        row = [
            country["ISO_A2"],
            group,
            country["ADMIN"],
            ]

        for value in row:
            assert DELIMITER not in value

        sys.stdout.write((
            (DELIMITER + u" ").join(row) + "\n"
        ).encode("utf-8"))



def main():
    log.addHandler(logging.StreamHandler())

    usage = """%prog SHP

SHP    World admin shapefile.
"""

    parser = OptionParser(usage=usage)
    parser.add_option("-v", "--verbose", action="count", dest="verbose",
                      help="Print verbose information for debugging.", default=0)
    parser.add_option("-q", "--quiet", action="count", dest="quiet",
                      help="Suppress warnings.", default=0)

    (options, args) = parser.parse_args()
    args = [arg.decode(sys.getfilesystemencoding()) for arg in args]

    log_level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG,)[
        max(0, min(3, 1 + options.verbose - options.quiet))]

    log.setLevel(log_level)

    if not len(args) == 1:
        parser.print_usage()
        sys.exit(1)

    (shp_path, ) = args

    world2group(shp_path)
    
    

if __name__ == "__main__":
    main()
