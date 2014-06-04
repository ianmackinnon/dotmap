#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
from optparse import OptionParser
from collections import defaultdict

import shapefile

from geometry import Geometry



DELIMITER = u";"



log = logging.getLogger('worldgeo')



def dump_csv(sf):
    row_targets = ("ISO_A2", "ADMIN", "SUBREGION")
    row_target_ids = [sf.get_field(name) for name in row_targets]
    for record in sf.records():
        values = [record[id_].decode("utf-8") for id_ in row_target_ids]
        if values[0] == u"-99":
            continue

        for value in values:
            assert DELIMITER not in value
        sys.stdout.write((
            (DELIMITER + u" ").join(values) + "\n"
        ).encode("utf-8"))



def trunc(f, n=6):
    m = 10**n
    return float(int(f * m + float(cmp(f, 0))*.5)) / m



def shp2geo(sf):
    geometry = Geometry()
    index_admin = sf.get_field("ADMIN")
    index_iso2 = sf.get_field("ISO_A2")

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



def dump_geo(sf):
    geometry = shp2geo(sf)
    print geometry.render()



def attach_field_index(sf):
    field_names = [field[0] for field in sf.fields[1:]]
    def get_field(name):
        return field_names.index(name)
    sf.get_field = get_field



def worldgeo(shp_path, dump=None):
    log.info(shp_path)
    sf = shapefile.Reader(shp_path)
    attach_field_index(sf)

    if dump:
        dump_csv(sf)
        return

    dump_geo(sf)



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
    parser.add_option("-l", "--list", action="store_true", dest="dump",
                      help="List countries as CSV of iso2, name.", default=None)

    (options, args) = parser.parse_args()
    args = [arg.decode(sys.getfilesystemencoding()) for arg in args]

    log_level = (logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG,)[
        max(0, min(3, 1 + options.verbose - options.quiet))]

    log.setLevel(log_level)

    if not len(args) == 1:
        parser.print_usage()
        sys.exit(1)

    (shp_path, ) = args

    worldgeo(shp_path, options.dump)
    
    

if __name__ == "__main__":
    main()
