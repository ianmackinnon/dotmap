#!/usr/bin/env python
#-*- coding utf-8 -*-

import re
import sys
import shlex

from mako.template import Template
from mako import exceptions



class Geometry(object):

    geo_template = """PGEOMETRY V5
NPoints ${len(geometry.points)} NPrims ${len(geometry.prims)}
NPointGroups 0 NPrimGroups 0
NPointAttrib ${len(geometry.point_attrs)} NVertexAttrib 0 NPrimAttrib ${len(geometry.prim_attrs)} NAttrib ${int(bool(geometry.attr_names))}

%if len(geometry.point_attrs):
PointAttrib

%for p, (name, point_attr) in enumerate(geometry.point_attrs.items()):
%if name in geometry.point_attr_string_dict.keys():
<% index = geometry.point_attr_string_dict[name] %>\
${name} 1 index ${len(index)} \\
%for text in index:
"${text.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"')}" \\
%endfor

%else:
${name} ${point_attr["length"]} ${point_attr["type"] == int and "int" or "float"} ${" ".join([str(v) for v in point_attr["default"]])}
%endif
%endfor
%endif

%for p, point in enumerate(geometry.points):
${"%f %f %f %f" % (point[0], point[1], point[2], 1.0)} \\
%if geometry.point_attrs:
(${"\t".join([" ".join([str(v) for v in geometry.point_attrs[key]["values"][p]]) for key in geometry.point_attrs])}) \\
%endif

%endfor


%if len(geometry.prims):

%if len(geometry.prim_attrs):
PrimitiveAttrib

%for p, (name, prim_attr) in enumerate(geometry.prim_attrs.items()):
%if name in geometry.prim_attr_string_dict.keys():
<% index = geometry.prim_attr_string_dict[name] %>\
${name} 1 index ${len(index)} \\
%for text in index:
"${text.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"')}" \\
%endfor

%else:
${name} ${prim_attr["length"]} ${prim_attr["type"] == int and "int" or "float"} ${" ".join([str(v) for v in prim_attr["default"]])}
%endif
%endfor
%endif

%for p, prim in enumerate(geometry.prims):
Poly ${len(prim["points"])} ${"<" if prim["closed"] else ":"} ${" ".join([str(v) for v in prim["points"]])} \\
%if geometry.prim_attrs:
(${"\t".join([" ".join([str(v) for v in geometry.prim_attrs[key]["values"][p]]) for key in geometry.prim_attrs])}) \\
%endif

%endfor

%endif

%if geometry.attr_names:
DetailAttrib
varmap 1 index ${len(geometry.attr_names)} ${" ".join(['"%s -> %s"' % (name, name) for name in geometry.attr_names])}
 (0)
%endif

beginExtra
endExtra
"""

    def __init__(self):
        self.points = []
        self.prims = []
        self.point_attrs = {}
        self.prim_attrs = {}
        self.point_attr_string_dict = {}
        self.prim_attr_string_dict = {}


    def add_point(self, x, y, z):
        self.points.append((x, y, z))
        return len(self.points) - 1

    def add_prim(self, point_numbers, closed=True):
        self.prims.append({"closed": closed, "points": point_numbers})
        return len(self.prims) - 1

    def set_scalar_attr(self, attributes, obj, type_, name, index, values):
        if not hasattr(values, "__len__"):
            values = [values]
        length = len(values)
        if not name in attributes:
            attributes[name] = {
                "type": type_,
                "length": length,
                "values": {},
                "default": [type_() for i in range(length)],
            }
        else:
            if attributes[name]["type"] != type_:
                raise TypeError("%s attribute '%s' already has type '%s'." % (obj, name, attributes[name]["type"]))
            if attributes[name]["length"] != length:
                raise TypeError("%s attribute '%s' already has length '%s'." % (obj, name, attributes[name]["length"]))                
        attributes[name]["values"][index] = values
        
    def set_point_attr_int(self, name, index, values):
        self.set_scalar_attr(self.point_attrs, "Point", int, name, index, values)

    def set_point_attr_float(self, name, index, values):
        self.set_scalar_attr(self.point_attrs, "Point", float, name, index, values)

    def set_point_attr_string(self, name, index, value):
        assert hasattr(name, "strip")
        assert index == int(index)
        if not name in self.point_attr_string_dict:
            self.point_attr_string_dict[name] = []
        if not value in self.point_attr_string_dict[name]:
            self.point_attr_string_dict[name].append(value)
        value = self.point_attr_string_dict[name].index(value)
        self.set_scalar_attr(self.point_attrs, "Point", str, name, index, value)


    def set_prim_attr_int(self, name, index, values):
        self.set_scalar_attr(self.prim_attrs, "Prim", int, name, index, values)

    def set_prim_attr_float(self, name, index, values):
        self.set_scalar_attr(self.prim_attrs, "Prim", float, name, index, values)

    def set_prim_attr_string(self, name, index, value):
        assert hasattr(name, "strip")
        assert index == int(index)
        if not name in self.prim_attr_string_dict:
            self.prim_attr_string_dict[name] = []
        if not value in self.prim_attr_string_dict[name]:
            self.prim_attr_string_dict[name].append(value)
        value = self.prim_attr_string_dict[name].index(value)
        self.set_scalar_attr(self.prim_attrs, "Prim", str, name, index, value)


    def get_point_attr(self, name, index):
        assert name in self.point_attrs, "No such point attribute '%s'." % name
        value = self.point_attrs[name]["values"].get(index, 0) 
        if hasattr(value, "__len__") and len(value) == 1:
            value = value[0]
        if self.point_attrs[name]["type"] == str:
            value = self.point_attr_string_dict[name][value]
        return value

    def get_prim_attr(self, name, index):
        assert name in self.prim_attrs, "No such primitive attribute '%s'." % name
        value = self.prim_attrs[name]["values"].get(index, 0) 
        if hasattr(value, "__len__") and len(value) == 1:
            value = value[0]
        if self.prim_attrs[name]["type"] == str:
            value = self.prim_attr_string_dict[name][value]
        return value

    @property
    def attr_names(self):
        return self.point_attrs.keys() + self.prim_attrs.keys()

    def render(self):
        try:
            return Template(self.geo_template).render(geometry=self)
        except:
            print exceptions.text_error_template().render()



def parse_index(text):
    parts = shlex.split(text)
    length = int(parts.pop(0))
    assert len(parts) == length
    return parts



def parse_attribute_definition(line, attributes):
    regex_string = "(\w+) (\d+) (\w+) (.+)$"
    regex = re.compile(regex_string)
    match = regex.match(line)
    if match:
        name, length, type_, values = match.groups()
        length = int(length)
        if type_ == "index":
            assert length == 1
            values = parse_index(values)
        else:
            values = values.split()
            if type_ == "int":
                values = [int(v) for v in values]
            elif type_ == "float":
                values = [float(v) for v in values]
            else:
                raise TypeError, type_
            assert len(values) == length
        attributes.append({
            "name": name,
            "type": type_,
            "values": values,
        })
        return True

def attributes_length(attributes):
    total = 0
    for attr in attributes:
        if attr["type"] == "index":
            total += 1
        else:
            total += len(attr["values"])
    return total

def parse_attr_values(attrs, attributes, count,
                      set_int, set_float, set_string):
    assert len(attrs) == attributes_length(attributes), repr((
        len(attrs), attributes_length(attributes),
        attrs, attributes
        ))
    for attr in attributes:
        if attr["type"] == "index":
            value = int(attrs.pop(0))
            set_string(attr["name"], count, attr["values"][value])
            continue
        length = len(attr["values"])
        values = attrs[:length]
        attrs = attrs[length:]
        if attr["type"] == "int":
            values = [int(v) for v in values]
            set_int(attr["name"], count, values)
        elif attr["type"] == "float":
            values = [float(v) for v in values]
            set_float(attr["name"], count, values)
        else:
            raise TypeError, "Type '%s' not recognised." % attr["type"]



def read(path):
    geo_file = open(path)
    geo = Geometry()
    headlines = [
        ("PGEOMETRY V5", ()),
        ("NPoints (\d+) NPrims (\d+)", ("npoints", "nprims")),
        ("NPointGroups (\d+) NPrimGroups (\d+)", ("npointgroups", "nprimgroups")),
        ("NPointAttrib (\d+) NVertexAttrib (\d+) NPrimAttrib (\d+) NAttrib (\d+)", ("npointattrib", "nvertexattrib", "nprimattrib", "nattrib")),
        ]

    attr = {}
    mode = None
    point_attributes = []
    prim_attributes = []
    points = 0
    prims = 0
            


    for line in geo_file.readlines():
        line = line.strip()
        if not line:
            continue

        if headlines:
            regex_string, keys = headlines.pop(0)
            regex = re.compile(regex_string)
            match = regex.match(line)
            if not match:
                print "Failed to match '%s' with line '%s'." % (regex_string, line)
                sys.exit(1)
            values = [int(x) for x in match.groups()]
            attr.update(dict(zip(keys, values)))
            continue
        
        if line == "PointAttrib":
            mode = "PointAttrib"
            continue
        if line == "PrimitiveAttrib":
            mode = "PrimitiveAttrib"
            continue
        if line == "DetailAttrib":
            break

        if mode == "PointAttrib":
            if parse_attribute_definition(line, point_attributes):
                continue
            else:
                mode = "Point"

        if mode == "PrimitiveAttrib":
            if parse_attribute_definition(line, prim_attributes):
                continue
            elif re.match("Run \d+ Poly$", line):
                continue
            else:
                mode = "Prim"

        if mode == "Point":
            line = line.replace("(", "").replace(")", "")
            parts = re.split("\s+", line)
            x, y, z, w = (float(v) for v in parts[:4])
            attrs = parts[4:]
            geo.add_point(x, y, z)
            parse_attr_values(attrs, point_attributes, points,
                              geo.set_point_attr_int,
                              geo.set_point_attr_float,
                              geo.set_point_attr_string,
                              )
            points += 1

        if mode == "Prim":
            line = line.replace("[", "").replace("]", "")
            parts = re.split("\s+", line)
            if parts[0] == "Poly":
                parts.pop(0)
            length = int(parts.pop(0))
            closed = parts.pop(0) == "<"
            point_list = parts[:length]
            attrs = parts[length:]
            geo.add_prim(point_list, closed=closed)
            parse_attr_values(attrs, prim_attributes, prims,
                              geo.set_prim_attr_int,
                              geo.set_prim_attr_float,
                              geo.set_prim_attr_string,
                              )
            prims += 1

    return geo
