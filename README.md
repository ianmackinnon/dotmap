# Dotmap

Generate simple maps in which clearly represent all states at the same scale.


## Goals

-   All countries must be visible and of a comfortable minimum size
-   Any country should be easily selectable on a smartphone touchscreen without scaling the map
-   Country position should be roughly accurate
-   Country size should be roughly representative of area and population


## Included map sets

-   ISO 3166-1


## Generate map data

-   Run the map generate server:

    make -C code/generate generate
    
-   Navigate to http://localhost:8000
-   Tweak the simulation
-   Click the save button
-   Copy the output file (watch the browser console or the generate server output for paths)









