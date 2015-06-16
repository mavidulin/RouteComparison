# -*- coding: utf-8 -*-
import datetime as DT

from osgeo import ogr

from utility import Utility

UTILITY = Utility()


class RoutesProcessor(object):
    """This class contains methods for processing routes geometries and
    attributes and saving results to files.
    """

    def process_geometry(
            self,
            pgrouting_data,
            google_data,
            mapquest_data,
            route_number,
            foldername):
        """Processes provided routes geometries and executes geometries
        export function. It calculates differences between provided routes.

        :arg pgrouting_data: dictionary with geometry and attribute data for
            pgrouting route.
        :type pgrouting_data: dictionary

        :arg google_data: dictionary with geometry and attribute data for
            google route.
        :type google_data: dictionary

        :arg mapquest_data: dictionary with geometry and attribute data for
            mapquest route.
        :type mapquest_data: dictionary

        :arg route_number: ordinal of start-end location pair in input file
        :type route_number: integer

        :arg foldername: path to directory for saving results
        :type foldername: string

        """
        # Difference between pg_route and mapquest route.
        # Returns pg_route geom where two routes differentiate.
        pg_mapquest_diff = pgrouting_data['route_shapely'].difference(
            mapquest_data['route_buffer_shapely']
        )

        # Difference between mapquest and pg route.
        # Returns mapquest_route geom where two routes differentiate.
        mapquest_pg_diff = mapquest_data['route_shapely'].difference(
            pgrouting_data['route_buffer_shapely']
        )

        # Difference between pg_route and google route.
        # Returns pg_route geom where two routes differentiate.
        pg_google_diff = pgrouting_data['route_shapely'].difference(
            google_data['route_buffer_shapely']
        )

        # Difference between google and pg route.
        # Returns google_route geom where two routes differentiate.
        google_pg_diff = google_data['route_shapely'].difference(
            pgrouting_data['route_buffer_shapely']
        )

        # Difference between google and mapquest route.
        # Returns google geom where two routes differentiate.
        google_mapquest_diff = google_data['route_shapely'].difference(
            mapquest_data['route_buffer_shapely']
        )

        # Difference between mapquest and google route.
        # Returns mapquest_route geom where two routes differentiate.
        mapquest_google_diff = mapquest_data['route_shapely'].difference(
            google_data['route_buffer_shapely']
        )

        # Convert route difference geom from shapely to ogr (for export).
        pg_mapquest_diff_ogr = ogr.CreateGeometryFromWkb(pg_mapquest_diff.wkb)
        mapquest_pg_diff_ogr = ogr.CreateGeometryFromWkb(mapquest_pg_diff.wkb)
        pg_google_diff_ogr = ogr.CreateGeometryFromWkb(pg_google_diff.wkb)
        google_pg_diff_ogr = ogr.CreateGeometryFromWkb(google_pg_diff.wkb)
        google_mapquest_diff_ogr = ogr.CreateGeometryFromWkb(
            google_mapquest_diff.wkb
        )
        mapquest_google_diff_ogr = ogr.CreateGeometryFromWkb(
            mapquest_google_diff.wkb
        )

        self.export_geometries(
            pgrouting_data=pgrouting_data,
            google_data=google_data,
            mapquest_data=mapquest_data,
            pg_mapquest_diff_ogr=pg_mapquest_diff_ogr,
            mapquest_pg_diff_ogr=mapquest_pg_diff_ogr,
            pg_google_diff_ogr=pg_google_diff_ogr,
            google_pg_diff_ogr=google_pg_diff_ogr,
            google_mapquest_diff_ogr=google_mapquest_diff_ogr,
            mapquest_google_diff_ogr=mapquest_google_diff_ogr,
            route_number=route_number,
            foldername=foldername,
        )

    def export_geometries(
            self,
            pgrouting_data, google_data, mapquest_data,
            pg_mapquest_diff_ogr, mapquest_pg_diff_ogr,
            pg_google_diff_ogr, google_pg_diff_ogr,
            google_mapquest_diff_ogr, mapquest_google_diff_ogr,
            route_number, foldername):

        """Executes export of routes geometries to GeoJson files.

        :arg pgrouting_data: dictionary with geometry and attribute data for
            pgrouting route.
        :type pgrouting_data: dictionary

        :arg google_data: dictionary with geometry and attribute data for
            google route.
        :type google_data: dictionary

        :arg mapquest_data: dictionary with geometry and attribute data for
            mapquest route.
        :type mapquest_data: dictionary

        :arg pg_mapquest_diff_ogr: ogr geometry that respresent difference
            between pgrouting and mapquest route.
        :type pg_mapquest_diff_ogr: osgeo.ogr.Geometry

        :arg mapquest_pg_diff_ogr: ogr geometry that respresent difference
            between mapquest and pgrouting route.
        :type mapquest_pg_diff_ogr: osgeo.ogr.Geometry

        :arg pg_google_diff_ogr: ogr geometry that respresent difference
            between pgrouting and google route.
        :type pg_google_diff_ogr: osgeo.ogr.Geometry

        :arg google_pg_diff_ogr: ogr geometry that respresent difference
            between google and pgrouting route.
        :type google_pg_diff_ogr: osgeo.ogr.Geometry

        :arg mapquest_google_diff_ogr: ogr geometry that respresent difference
            between mapquest and google route.
        :type mapquest_google_diff_ogr: osgeo.ogr.Geometry

        :arg google_mapquest_diff_ogr: ogr geometry that respresent difference
            between google and mapquest route.
        :type google_mapquest_diff_ogr: osgeo.ogr.Geometry

        :arg route_number: ordinal of start-end location pair in input file
        :type route_number: integer

        :arg foldername: path to directory for saving results
        :type foldername: string

        """
        UTILITY.create_geojson_file(
            geom=pgrouting_data['route_ogr'],
            geomtype=ogr.wkbMultiLineString,
            filename=foldername + '/pg_route_' + str(route_number)
        )
        UTILITY.create_geojson_file(
            geom=pgrouting_data['route_buffer_ogr'],
            geomtype=ogr.wkbMultiPolygon,
            filename=foldername + '/pg_buffer_' + str(route_number)
        )

        UTILITY.create_geojson_file(
            geom=google_data['route_ogr'],
            geomtype=ogr.wkbMultiLineString,
            filename=foldername + '/google_route_' + str(route_number)
        )
        UTILITY.create_geojson_file(
            geom=google_data['route_buffer_ogr'],
            geomtype=ogr.wkbMultiPolygon,
            filename=foldername + '/google_buffer_' + str(route_number)
        )

        UTILITY.create_geojson_file(
            geom=mapquest_data['route_ogr'],
            geomtype=ogr.wkbLineString,
            filename=foldername + '/mapquest_route_' + str(route_number)
        )
        UTILITY.create_geojson_file(
            geom=mapquest_data['route_buffer_ogr'],
            geomtype=ogr.wkbMultiPolygon,
            filename=foldername + '/mapquest_buffer_' + str(route_number)
        )

        UTILITY.create_geojson_file(
            geom=pg_mapquest_diff_ogr,
            geomtype=ogr.wkbMultiLineString,
            filename=foldername + '/pg_mapquest_diff_' + str(route_number)
        )

        UTILITY.create_geojson_file(
            geom=mapquest_pg_diff_ogr,
            geomtype=ogr.wkbMultiLineString,
            filename=foldername + '/mapquest_pg_diff_' + str(route_number)
        )

        UTILITY.create_geojson_file(
            geom=pg_google_diff_ogr,
            geomtype=ogr.wkbMultiLineString,
            filename=foldername + '/pg_google_diff_' + str(route_number)
        )

        UTILITY.create_geojson_file(
            geom=google_pg_diff_ogr,
            geomtype=ogr.wkbMultiLineString,
            filename=foldername + '/google_pg_diff_' + str(route_number)
        )

        UTILITY.create_geojson_file(
            geom=google_mapquest_diff_ogr,
            geomtype=ogr.wkbMultiLineString,
            filename=foldername + '/google_mapquest_diff_' + str(route_number)
        )

        UTILITY.create_geojson_file(
            geom=mapquest_google_diff_ogr,
            geomtype=ogr.wkbMultiLineString,
            filename=foldername + '/mapquest_google_diff_' + str(route_number)
        )

    def process_attributes(
            self,
            pgrouting_data,
            google_data,
            mapquest_data,
            route_number,
            foldername):
        """Executes function for calculating numerical attribute data
        differences between two routes and function for writing route details
        and differences to file.

        :arg pgrouting_data: dictionary with geometry and attribute data for
            pgrouting route.
        :type pgrouting_data: dictionary

        :arg google_data: dictionary with geometry and attribute data for
            google route.
        :type google_data: dictionary

        :arg mapquest_data: dictionary with geometry and attribute data for
            mapquest route.
        :type mapquest_data: dictionary

        :arg route_number: ordinal of start-end location pair in input file
        :type route_number: integer

        :arg foldername: path to directory for saving results
        :type foldername: string

        """

        pg_mapquest_diff_attribute_data = (
            self.get_route_detail_differences(
                route1_data=pgrouting_data,
                route2_data=mapquest_data
            )
        )

        pg_google_diff_attribute_data = (
            self.get_route_detail_differences(
                route1_data=pgrouting_data,
                route2_data=google_data
            )
        )

        mapquest_google_diff_attribute_data = (
            self.get_route_detail_differences(
                route1_data=mapquest_data,
                route2_data=google_data
            )
        )

        self.write_details_to_file(
            pgrouting_data=pgrouting_data,
            google_data=google_data,
            mapquest_data=mapquest_data,
            pg_mapquest_diff_attribute_data=pg_mapquest_diff_attribute_data,
            pg_google_diff_attribute_data=pg_google_diff_attribute_data,
            mapquest_google_diff_attribute_data=(
                mapquest_google_diff_attribute_data),
            route_number=route_number,
            foldername=foldername
        )

    def get_route_detail_differences(self, route1_data, route2_data):
        """
        Calculates numerical attribute data differences between two routes.
        Numerical attribute data are driving timea and route length.
        Calculated differences are:
            - driving time difference
            - length difference
            - driving time difference in percentage
            - length difference in percentage

        :arg route1_data: dictionary with data for first route
        :type route1_data: dictionary

        :arg route2_data: dictionary with data for second route
        :type route2_data: dictionary

        :returns: calculated differences between two routes
        :rtype: dictionary

        """
        # Driving time difference between route1 and route2 in seconds.
        route1_route2_driving_time_diff_sec = abs(
            route1_data['driving_time']['sec'] -
            route2_data['driving_time']['sec']
        )

        # Driving time difference between route1 and route2 in HMS.
        route1_route2_driving_time_diff_hms = DT.timedelta(
            seconds=route1_route2_driving_time_diff_sec
        )

        # Driving time difference between route1 and route2 in percentage.
        route1_route2_driving_time_percent_diff = round(
            (
                (
                    route1_route2_driving_time_diff_sec /
                    route2_data['driving_time']['sec']
                ) * 100
            ),
            1
        )

        # Length difference between route1 and route2 in kilometers.
        route1_route2_length_diff = abs(
            route1_data['len'] - route2_data['len']
        )

        # Length difference between route1 and route2 in percentage.
        route1_route2_length_percent_diff = round(
            (route1_route2_length_diff / route2_data['len']) * 100, 1
        )

        return {
            'driving_time_diff_hms': route1_route2_driving_time_diff_hms,
            'driving_time_percent_diff':
            route1_route2_driving_time_percent_diff,
            'length_diff': route1_route2_length_diff,
            'length_percent_diff': route1_route2_length_percent_diff,
        }

    def write_details_to_file(
            self,
            pgrouting_data,
            google_data,
            mapquest_data,
            pg_mapquest_diff_attribute_data,
            pg_google_diff_attribute_data,
            mapquest_google_diff_attribute_data,
            route_number,
            foldername):

        """Writes routes detail and differences between routes to file.

        .. note:: MISSING GOOGLE DETAILED DATA!

        :arg pgrouting_data: dictionary with geometry and attribute data for
            pgrouting route.
        :type pgrouting_data: dictionary

        :arg google_data: dictionary with geometry and attribute data for
            google route.
        :type google_data: dictionary

        :arg mapquest_data: dictionary with geometry and attribute data for
            mapquest route.
        :type mapquest_data: dictionary

        :arg pg_mapquest_diff_attribute_data: dictionary with differences
            between pgrouting and mapquest route, like length and driving time.
        :type pg_mapquest_diff_attribute_data: dictionary

        :arg route_number: ordinal of start-end location pair in input file
        :type route_number: integer

        :arg foldername: path to directory for saving file
        :type foldername: string

        """
        # Open file for writing in route output directory.
        details_file = open(foldername + '/details.txt', 'w')

        # Write PgRouting route details to file.
        details_file.write(
            self.compose_route_details_text(
                route_data=pgrouting_data,
                title='PgRouting route ' + str(route_number)
            )
        )

        # Write MapQuest route details to file.
        details_file.write(
            self.compose_route_details_text(
                route_data=mapquest_data,
                title='MapQuest route ' + str(route_number)
            )
        )

        # Write Google route details to file.
        details_file.write(
            self.compose_route_details_text(
                route_data=google_data,
                title='Google route ' + str(route_number)
            )
        )

        # Write PgRouting and MapQuest route differences to file.
        details_file.write(
            self.compose_route_comparison_text(
                diff_data=pg_mapquest_diff_attribute_data,
                title='PgRouting vs. MapQuest - route ' + str(route_number)
            )
        )

        # Write PgRouting and Google route differences to file.
        details_file.write(
            self.compose_route_comparison_text(
                diff_data=pg_google_diff_attribute_data,
                title='PgRouting vs. Google - route ' + str(route_number)
            )
        )

        # Write Mapquest and Google route differences to file.
        details_file.write(
            self.compose_route_comparison_text(
                diff_data=mapquest_google_diff_attribute_data,
                title='Mapquest vs. Google - route ' + str(route_number)
            )
        )

        details_file.close()

    def compose_route_details_text(self, route_data, title):
        """Creates a string with route details that will be written to file.

        :arg route_data: dictionary with geometry and attribute data for a
            route.
        :type route_data: dictionary

        :arg title: title/heading for part of the text,
            e.g. 'PgRouting route 1 details'
        :type title: string

        :returns: string with composed text
        :rtype: string

        """
        output = (
            '{title}\n\n'
            'distance via route: {distance} km\n'
            'travell time: {time} (h:m:s)\n\n'
            '{h_divider}\n\n'

        ).format(
            title=title,
            distance=route_data['len'],
            time=route_data['driving_time']['hms'],
            h_divider='-' * 40
        )

        return output

    def compose_route_comparison_text(self, diff_data, title):
        """Creates a string with text that will be written to file.
        Text contains details about attribute data differences between two
        routes. Differences are something like length and driving time
        differences.

        :arg diff_data: dictionary with differences between two routes,
            like length and driving time differences.
        :type diff_data: dictionary

        :returns: string with composed text
        :rtype: string

        """
        output = (
            '{title}\n\n'
            'length difference: {length_diff} km, {length_diff_percent}%\n'
            'time difference: {time_diff} (h:m:s), {time_diff_percent}%\n\n'
            '{h_divider}\n\n'

        ).format(
            title=title,
            length_diff=diff_data['length_diff'],
            length_diff_percent=diff_data['length_percent_diff'],
            time_diff=diff_data['driving_time_diff_hms'],
            time_diff_percent=diff_data['driving_time_percent_diff'],
            h_divider='-' * 40
        )

        return output
