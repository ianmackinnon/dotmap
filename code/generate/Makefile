SHELL := /bin/bash
.PHONY : all clean \
	d3-patch

TMP := "/tmp/dotmap"
D3_URL := https://raw.githubusercontent.com/mbostock/d3/master/d3.js


all :

clean :


generate : d3.patched.js
	./server.py --data=/tmp

d3.patched.js : d3.orig.js d3.patch
	patch $^ -o $@

d3-patch : d3.orig.js
	-diff -c d3.orig.js d3.patched.js > d3.patch

d3.orig.js :
	wget -O $(TMP) $(D3_URL)
	mv $(TMP) $@


