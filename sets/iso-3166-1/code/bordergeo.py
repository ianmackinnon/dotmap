#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import codecs
import logging
from optparse import OptionParser
from collections import defaultdict

import shapefile

from geometry import Geometry



DELIMITER = u";"



log = logging.getLogger('bordergeo')



def trunc(f, n=6):
    m = 10**n
    return float(int(f * m + float(cmp(f, 0))*.5)) / m



def shp2geo(sf, iso32, border_switch, border_deny):
    geometry = Geometry()

    index_iso3_left = sf.get_field("adm0_a3_l")
    index_iso3_right = sf.get_field("adm0_a3_r")
    index_type = sf.get_field("type")

    p = 0
    for s, shaperecord in enumerate(sf.records()):
        shaperecord = sf.shapeRecord(s)
        iso3_left = shaperecord.record[index_iso3_left]
        iso3_right = shaperecord.record[index_iso3_right]
        type_ = shaperecord.record[index_type]

        try:
            iso2_left = iso32[iso3_left]
            iso2_right = iso32[iso3_right]
        except KeyError as e:
            log.warning(repr((iso3_left, iso3_right, str(e))))
            raise e

        border_key = tuple(sorted([iso2_left, iso2_right]))

        if border_key in border_switch:
            log.warning(repr(border_switch))
            log.warning("switch %s -> %s" % (repr(border_key), repr(border_switch[border_key])))
            iso2_left, iso2_right = border_switch[border_key]
            border_key = tuple(sorted([iso2_left, iso2_right]))            
            log.info(shaperecord.shape.parts)

        if border_key in border_deny:
            log.warning("inhibit %s" % repr(border_key))
            continue

        if iso2_left == iso2_right:
            continue

        if hasattr(shaperecord.shape, "parts"):
            parts = shaperecord.shape.parts
        else:
            log.warning(s)
            parts = []
        part_shapes = []
        for i, point in enumerate(shaperecord.shape.points):
            if i in parts:
                part_shapes.append([])
            part_shapes[-1].append(point)
        p += len(part_shapes)
        for part_shape in part_shapes:
            point_numbers = []
            for point in part_shape[:]:  # because it's open
                point_number = geometry.add_point(trunc(point[0]), trunc(point[1]), 0.0)
                point_numbers.append(point_number)
            prim_number = geometry.add_prim(point_numbers, closed=False)
            
            geometry.set_prim_attr_string('iso2_left', prim_number, iso2_left)
            geometry.set_prim_attr_string('iso2_right', prim_number, iso2_right)
            geometry.set_prim_attr_string('type', prim_number, type_)
            geometry.set_prim_attr_int('prim', prim_number, prim_number)

    d = defaultdict(int)
    for p, point in enumerate(geometry.points):
        d[point] += 1
    for p, point in enumerate(geometry.points):
        geometry.set_point_attr_int('freq', p, d[point])
    
    return geometry



def dump_geo(sf, iso32, border_deny, border_switch):
    geometry = shp2geo(sf, iso32, border_deny, border_switch)
    print geometry.render()



def attach_field_index(sf):
    field_names = [field[0] for field in sf.fields[1:]]
    def get_field(name):
        return field_names.index(name)
    sf.get_field = get_field



def get_iso32(csv_file):
    iso32 = {}
    for line in csv_file:
        line = line.strip()
        if not line:
            continue
        parts = line.split(DELIMITER)
        assert len(parts) >= 3, parts
        parts = [part.strip() for part in parts[:3]]
        iso2, iso3, ison = parts
        assert len(iso2) == 2, iso2
        assert len(iso3) == 3, iso3
        iso32[iso3] = iso2
    return iso32



def get_border(csv_file, is_dict=False):
    log.info(is_dict)
    border = []
    for line in csv_file:
        line = line.split("#")[0]
        line = line.strip()
        if not line:
            continue
        parts = line.split(DELIMITER)
        parts = [part.strip() for part in parts]
        for i, part in enumerate(parts):
            assert len(part) == 2, part
        if is_dict:
            assert len(parts) == 4, repr(parts)
            border.append((tuple(sorted(parts[:2])), tuple(sorted(parts[2:]))))
        else:
            assert len(parts) == 2, repr(parts)
            border.append(tuple(sorted(parts)))
    if is_dict:
        border = dict(border)
        log.info(repr(border))
    return border



def worldgeo(shp_path, iso_csv_path,
             border_switch_csv_path, border_deny_csv_path):
    log.info(shp_path)
    sf = shapefile.Reader(shp_path)
    attach_field_index(sf)

    log.info(iso_csv_path)
    with codecs.open(iso_csv_path, "r", "utf-8") as iso_csv_file:
        iso32 = get_iso32(iso_csv_file)

    log.info(border_switch_csv_path)
    with codecs.open(border_switch_csv_path, "r", "utf-8") as csv_file:
        border_switch = get_border(csv_file, is_dict=True)

    log.info(border_deny_csv_path)
    with codecs.open(border_deny_csv_path, "r", "utf-8") as csv_file:
        border_deny = get_border(csv_file)

    dump_geo(sf, iso32, border_switch, border_deny)



def main():
    log.addHandler(logging.StreamHandler())

    usage = """%prog SHP ISO_CSV BORDERS_CSV

SHP          World admin shapefile.
ISO_CSV      CSV of "ISO2, ISO3, ISON".
BORDERS_SWITCH_CSV  CSV of ISO2 codes of borders to switch.
BORDERS_DENY_CSV  CSV of ISO2 codes of borders to inhibit.
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

    if not len(args) == 4:
        parser.print_usage()
        sys.exit(1)

    (shp_path, iso_csv_path, border_switch_csv_path, border_deny_csv_path) = args

    worldgeo(shp_path, iso_csv_path, border_switch_csv_path, border_deny_csv_path)
    
    

if __name__ == "__main__":
    main()
