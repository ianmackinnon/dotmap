SHELL := /bin/bash
.PHONY : all clean \
	test-shape

TMP := "/tmp/dotmap"
AGENT := "Mozilla/5.0 (Windows NT 5.2; rv:2.0.1) Gecko/20100101 Firefox/4.0.1"
COUNTRY_URL := http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip
BORDER_LAND_URL := http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_boundary_lines_land.zip
BORDER_SEA_URL := http://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_boundary_lines_maritime_indicator.zip
DATA_CODES_URL := https://www.cia.gov/library/publications/the-world-factbook/appendix/appendix-d.html
POPULATION_URL := https://www.cia.gov/library/publications/the-world-factbook/rankorder/rawdata_2119.txt

COUNTRY := ne_10m_admin_0_countries
BORDER_LAND := ne_10m_admin_0_boundary_lines_land
BORDER_SEA := ne_10m_admin_0_boundary_lines_maritime_indicator

all : data/json/dots.json

clean :
	rm -f sources/natural-earth/*
	rm -f sources/iso/*
	rm -f sources/cia/*


sources/natural-earth/$(COUNTRY).zip :
	wget -O $(TMP) --user-agent=$(AGENT) $(COUNTRY_URL)
	mv $(TMP) $@

sources/natural-earth/$(COUNTRY).shp : sources/natural-earth/$(COUNTRY).zip
	unzip -d $(dir $@) $^
	touch $@

sources/natural-earth/$(BORDER_LAND).zip :
	wget -O $(TMP) --user-agent=$(AGENT) $(BORDER_LAND_URL)
	mv $(TMP) $@

sources/natural-earth/$(BORDER_LAND).shp : sources/natural-earth/$(BORDER_LAND).zip
	unzip -d $(dir $@) $^
	touch $@

sources/natural-earth/$(BORDER_SEA).zip :
	wget -O $(TMP) --user-agent=$(AGENT) $(BORDER_SEA_URL)
	mv $(TMP) $@

sources/natural-earth/$(BORDER_SEA).shp : sources/natural-earth/$(BORDER_SEA).zip
	unzip -d $(dir $@) $^
	touch $@

sources/iso/1.short.en.csv :
	cp /home/ianmackinnon/jobs/isostate/sources/$(notdir $@) $@

sources/cia/country-data-codes.html :
	wget -O $(TMP) --user-agent=$(AGENT) $(DATA_CODES_URL)
	mv $(TMP) $@

sources/cia/population.text :
	wget -O $(TMP) --user-agent=$(AGENT) $(POPULATION_URL)
	mv $(TMP) $@




data/csv/names.csv : sources/iso/1.short.en.csv
	cut -d ";" -f 1,4 $^ > $(TMP)
	mv $(TMP) $@

data/csv/codes.cia.csv : sources/cia/country-data-codes.html
	./code/cia_codes.py $^ > $(TMP)
	mv $(TMP) $@

data/csv/codes.csv : data/csv/names.csv data/csv/codes.cia.csv data/csv/codes.manual.csv
	../../code/combine.py -c $^ > $(TMP)
	mv $(TMP) $@

data/csv/population.cia.csv : sources/cia/population.text data/csv/codes.cia.csv
	./code/cia_population.py $^ > $(TMP)
	mv $(TMP) $@

data/csv/population.csv : data/csv/names.csv data/csv/population.cia.csv data/csv/population.manual.csv
	../../code/combine.py -c $^ > $(TMP)
	mv $(TMP) $@

data/csv/groups.ne.csv : sources/natural-earth/$(COUNTRY).shp
	code/world2group.py $^ > $(TMP)
	mv $(TMP) $@

data/csv/groups.csv : data/csv/names.csv data/csv/groups.ne.csv data/csv/groups.manual.csv
	../../code/combine.py -c $^ > $(TMP)
	mv $(TMP) $@


data/geo/world.geo : sources/natural-earth/$(COUNTRY).shp
	code/worldgeo.py $^ > $(TMP)
	mv $(TMP) $@

data/geo/border.geo : sources/natural-earth/$(BORDER_LAND).shp data/csv/codes.cia.csv data/csv/borders-switch.manual.csv data/csv/borders-deny.manual.csv
	code/bordergeo.py -v sources/natural-earth/$(BORDER_LAND).shp <(cat data/csv/codes.cia.csv data/csv/codes.manual.csv) data/csv/borders-switch.manual.csv data/csv/borders-deny.manual.csv > $(TMP)
	mv $(TMP) $@

data/geo/missing.geo : data/csv/landmass-latlon.manual.csv
	code/missinggeo.py $^ > $(TMP)
	mv $(TMP) $@

data/geo/world-3d-points.geo : houdini/world.hipnc data/geo/world.geo data/geo/missing.geo
	bash -c " \
	pushd /opt/hfs11.1.201/; \
	source houdini_setup_bash; \
	popd; \
	echo 'render obj/geo1/rop_world_3d_points' | hscript houdini/world.hipnc \
	"

data/geo/border-3d-points.geo : houdini/world.hipnc data/geo/border.geo
	bash -c " \
	pushd /opt/hfs11.1.201/; \
	source houdini_setup_bash; \
	popd; \
	echo 'render obj/geo1/rop_border_3d_points' | hscript houdini/world.hipnc \
	"

data/json/dots.json : data/geo/world-3d-points.geo data/geo/border-3d-points.geo data/csv/names.csv data/csv/groups.csv data/csv/population.csv
	./code/compile_json.py $^ > $(TMP)
	mv $(TMP) $@








test-shape : sources/natural-earth/$(COUNTRY).shp sources/iso/1.iso.en.csv
	@echo Any codes printed are countries missing from the shape file.
	@comm -23 <(cut -d ";" -f 1 sources/iso/1.iso.en.csv | sort) <(code/worldgeo.py sources/natural-earth/$(COUNTRY).shp --list | cut -d ";" -f 1 | sort)




