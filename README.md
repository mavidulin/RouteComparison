# RouteComparison

This project is done as a part of master thesis. 

The purpose of the program is to compare routes (shortest paths) returned from Google and Mapquest services and from locally stored OSM data by using Pgrouting.

For defined start-end location pairs the program gets routes from Google, Mapquest and Pgrouting. 
Then it calculates the differences in geometry, driving time and distance. 
Route geometry and difference geometry are written to geojson files, and driving time and distance are written to text file.

Guide:

1. Get OSM data in .osm format

2. Move .osm file to input_data directory

3. Install Postgresql, Postgis and Pgrouting (http://pgrouting.org/documentation.html) and create database with those extensions

4. Install osm2pgrouting (http://pgrouting.org/docs/tools/osm2pgrouting.html)

5. Import osm data to the database by using osm2pgrouting

6. Import osm restrictions data to database using /main/osmrestrictions2pgrouting.py

7. Get your Google and Mapquest api keys

8. Fill in the config.txt file in /main

9. Fill in locations.txt file for desired routes

10. Execute the program by running "python main.py" in terminal in /main dir

11. When exectuion is done, view output files in /output_data dir
