#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import codecs
import logging
from optparse import OptionParser
from collections import defaultdict

from geometry import Geometry



DELIMITER = u";"



log = logging.getLogger('worldgeo')



def trunc(f, n=6):
    m = 10**n
    return float(int(f * m + float(cmp(f, 0))*.5)) / m



def shp2geo(sf):
    index_admin = sf.get_field("ADMIN")
    index_iso2 = sf.get_field("ISO_A3")

    p = 0
    for s, shaperecord in enumerate(sf.records()):
        shaperecord = sf.shapeRecord(s)
        admin = shaperecord.record[index_admin]
        iso2 = shaperecord.record[index_iso2]

        parts = shaperecord.shape.parts
        part_shapes = []
        for i, point in enumerate(shaperecord.shape.points):
            if i in parts:
                part_shapes.append([])
            part_shapes[-1].append(point)
        p += len(part_shapes)
        for part_shape in part_shapes:
            point_numbers = []
            for point in part_shape[:-1]:  # because it's closed
                point_number = geometry.add_point(trunc(point[0]), trunc(point[1]), 0.0)
                point_numbers.append(point_number)
            prim_number = geometry.add_prim(point_numbers)
            
            geometry.set_prim_attr_string('iso2', prim_number, iso2)
            geometry.set_prim_attr_int('prim', prim_number, prim_number)
    log.warning(repr((s, p)))

    d = defaultdict(int)
    for p, point in enumerate(geometry.points):
        d[point] += 1
    for p, point in enumerate(geometry.points):
        geometry.set_point_attr_int('freq', p, d[point])
    
    return geometry



def missinggeo(csv_path):
    log.info(csv_path)

    with codecs.open(csv_path, "r", "utf-8") as csv_file:
        geometry = Geometry()
        p = 0
        for line in csv_file.read().splitlines():
            line = re.sub("#.*$", "", line)
            line = line.strip()
            if not line:
                continue
            parts = [part.strip() for part in line.split(DELIMITER)]
            (iso2, name) = parts[:2]
            (latitude, longitude) = [float(value) for value in parts[2:]]

            geometry.add_point(longitude, latitude, 0)
            geometry.set_point_attr_string("iso2", p, iso2)
            geometry.set_point_attr_string("name", p, name)
            p += 1

        sys.stdout.write(geometry.render().encode("utf-8"))



def main():
    log.addHandler(logging.StreamHandler())

    usage = """%prog CSV

CSV    CSV of missing country coordinates.
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

    (csv_path, ) = args

    missinggeo(csv_path)
    
    

if __name__ == "__main__":
    main()
