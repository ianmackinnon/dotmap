#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import codecs
import logging
from optparse import OptionParser

import geometry



log = logging.getLogger('compile_json.py')
DELIMITER = ";"



def compile_json(land_geo_path, border_geo_path,
                 name_csv_path, group_csv_path, population_csv_path):
    land = geometry.read(land_geo_path)
    border = geometry.read(border_geo_path)

    names = {}
    with codecs.open(name_csv_path, "r", "utf-8") as csv_file:
        for line in csv_file:
            line = line.strip()
            if not line:
                continue
            iso2, name = line.split(DELIMITER + " ")
            names[iso2] = name

    groups = {}
    with codecs.open(group_csv_path, "r", "utf-8") as csv_file:
        for line in csv_file:
            line = line.strip()
            if not line:
                continue
            iso2, group = line.split(DELIMITER + " ")[:2]
            groups[iso2] = group

    populations = {}
    with codecs.open(population_csv_path, "r", "utf-8") as csv_file:
        for line in csv_file:
            line = line.strip()
            if not line:
                continue
            iso2, population = line.split(DELIMITER + " ")[:2]
            populations[iso2] = int(population)

    data = {
        "nodes": [],
        "links": [],
    }
    iso2p = {}

    for p, point in enumerate(land.points):
        iso2 = land.get_point_attr("iso2", p)
        if iso2 == "-99":
            continue
        area  = land.get_point_attr("area", p)
        perimeter  = land.get_point_attr("perimeter", p)
        lat, lon, null = land.get_point_attr("uv", p)
        iso2p[iso2] = len(data["nodes"])
        data["nodes"].append({
            "code": iso2,
            "name": names[iso2],
            "group": groups.get(iso2, None),
            "population": populations[iso2],
            "x": lat,
            "y": lon,
            "area": area,
            "perimeter": perimeter,
            })

    for p, point in enumerate(border.points):
        source_iso = border.get_point_attr("iso2_a", p)
        target_iso = border.get_point_attr("iso2_b", p)
        source = iso2p[source_iso]
        target = iso2p[target_iso]
        perimeter  = border.get_point_attr("perimeter", p)
        uv = border.get_point_attr("uv", p)
        lat, lon, null = uv
        
        data["links"].append({
            "sourceIso": source_iso,
            "targetIso": target_iso,
            "source": source,
            "target": target,
            "perimeter": perimeter,
            "x": lat,
            "y": lon,
        })

    json.dump(data, sys.stdout, indent=2)



if __name__ == "__main__":
    log.addHandler(logging.StreamHandler())

    usage = """%prog LANDGEO BORDERGEO NAMECSV GROUPCSV"""

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

    if not len(args) == 5:
        parser.print_usage()
        sys.exit(1)

    land_geo_path, border_geo_path, name_csv_path, group_csv_path, population_csv_path = args

    compile_json(land_geo_path, border_geo_path,
                 name_csv_path, group_csv_path, population_csv_path)

