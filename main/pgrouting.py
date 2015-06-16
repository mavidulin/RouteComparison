# -*- coding: utf-8 -*-
import datetime as DT

from shapely import wkt as shapely_wkt
from osgeo import ogr

from utility import Utility

UTILITY = Utility()


class PgRouting(object):
    """This class handles pgrouting route.

    :arg cursor: psycopg cursor
    :type cursor: psycopg2._psycopg.cursor

    """

    def __init__(self, cursor):
        self.cursor = cursor

    def get_route_data(self, start_coords, end_coords):
        """Executes function for getting pgrouting ways vertices from provided
        coordinates, executes function for getting route with pgrouting.
        Converts route to shapely and ogr geometry, creates buffer around the
        route and executes function for calculating numerical attribute data
        like driving time and length.

        :arg start_coords: dictionary with route starting location coordinates,
            e.g. {"x": 15.5, "y": 45.5}
        :type start_coords: dictionary

        :arg end_coords: dictionary with route ending location coordinates,
            e.g. {"x": 15.5, "y": 45.5}
        :type end_coords: dictionary

        :returns: dictionary with pgrouting route data
        :rtype: dictionary

        """
        start_vertex_id, end_vertex_id = self.get_way_vertices_from_coords(
            start_coords=start_coords,
            end_coords=end_coords
        )

        raw_route, colnames = self.get_route_from_pgrouting(
            start_vertex_id=start_vertex_id,
            end_vertex_id=end_vertex_id
        )

        route_ogr = self.create_multiline_from_linesegments(
            raw_route=raw_route,
            colnames=colnames
        )
        route_shapely = shapely_wkt.loads(route_ogr.ExportToWkt())

        route_buffer_ogr = UTILITY.create_route_buffer(route=route_ogr)
        route_buffer_shapely = shapely_wkt.loads(
            route_buffer_ogr.ExportToWkt()
        )

        driving_time = self.sum_cost(
            raw_route=raw_route,
            colnames=colnames
        )

        route_length = self.sum_route_length(
            raw_route=raw_route,
            colnames=colnames
        )

        return {
            'route_ogr': route_ogr,
            'route_shapely': route_shapely,
            'route_buffer_ogr': route_buffer_ogr,
            'route_buffer_shapely': route_buffer_shapely,
            'driving_time': driving_time,
            'len': route_length,
        }

    def get_way_vertices_from_coords(self, start_coords, end_coords):
        """Gets nearest OSM way vertex for starting and ending location.

        :arg start_coords: dictionary with route starting location coordinates,
            e.g. {"x": 15.5, "y": 45.5}
        :type start_coords: dictionary

        :arg end_coords: dictionary with route ending location coordinates,
            e.g. {"x": 15.5, "y": 45.5}
        :type end_coords: dictionary

        :returns: tuple which cosists of OSM way vertex id nearest to starting
            and OSM way vertex id nearest to ending location
        :rtype: tuple

        """

        # Compose query for finding nearest vertex to location.
        sql_query_template = """
            SELECT id,
            ST_Distance(
                ST_GeomFromText('POINT({lon} {lat})',4326),
                the_geom
            ) AS distance
            FROM ways_vertices_pgr
            WHERE the_geom IS NOT NULL
            ORDER BY distance ASC LIMIT 1;
        """

        # Execute query for start coord.
        sql_query = sql_query_template.format(
            lon=start_coords['x'],
            lat=start_coords['y']
        )

        self.cursor.execute(sql_query)
        start_vertex = self.cursor.fetchone()

        # Execute query for end coord.
        sql_query = sql_query_template.format(
            lon=end_coords['x'],
            lat=end_coords['y']
        )

        self.cursor.execute(sql_query)
        end_vertex = self.cursor.fetchone()

        return (start_vertex[0], end_vertex[0])

    def get_route_from_pgrouting(self, start_vertex_id, end_vertex_id):
        """Gets route from OSM data in databse with pgrouting function.

        .. note:: Uses pgrouting Turn Restriction Shortest Path function.
            Query returns route as list of line segements. All returned columns
            are: gid, class_id, length, name, x1, y1, x2, y2, reverse_cost,
            rule, to_cost, maxspeed_forward, maxspeed_backward, osm_id,
            priority, the_geom, source, target, seq, node, edge, cost.

        :arg start_vertex_id: way vertex id from which route starts
        :type start_vertex_id: integer

        :arg end_vertex_id: way vertex id where route ends
        :type end_vertex_id: integer

        :returns: tuple consisted of raw route data and list of column names.
        :rtype: (list, list)

        """
        # Compose query for getting the best route with pgrouting.
        sql_query = """
            SELECT gid, ST_AsGeoJSON(the_geom) as the_geom, cost, length
            FROM ways JOIN (
                SELECT seq, id1 AS node, id2 AS edge, cost
                FROM pgr_trsp('SELECT gid AS id, source, target,
                    length / (maxspeed_forward) AS cost,
                    reverse_cost / (maxspeed_forward) AS reverse_cost
                    FROM ways', {start_id}, {end_id}, true, true,
                    'SELECT to_cost, to_edge AS target_id,
                    from_edge || coalesce('','' || via, '''') AS via_path
                    FROM restrictions WHERE
                    from_edge IS NOT NULL AND to_edge IS NOT NULL')
            ) as route ON ways.gid = route.edge;
        """.format(start_id=start_vertex_id, end_id=end_vertex_id)

        self.cursor.execute(sql_query)

        # Get route data.
        route = self.cursor.fetchall()
        # Get column names.
        colnames = [desc[0] for desc in self.cursor.description]

        return (route, colnames)

    def sum_cost(self, raw_route, colnames):
        """Calculates overall route cost.

        .. note:: Cost is "time" so we essentially calculate driving time.

        :arg raw_route: raw route data retreived from db with pgrouting
        :type raw_route: list

        :arg colnames: list of column names retreived from db with pgrouting
        :type colnames: list

        :returns: dictionary with driving time in seconds and in HMS fomat.
        :rtype: dictionary

        """
        cost = 0
        # For each segement in raw_route increase cost.
        for segment in raw_route:
            cost += segment[colnames.index('cost')]

        # Convert cost from decimal hours to h:m:s and seconds format.
        time_hms = DT.timedelta(seconds=cost * 60 * 60.0)
        time_sec = cost * 3600

        return {
            'hms': time_hms,
            'sec': time_sec
        }

    def sum_route_length(self, raw_route, colnames):
        """Calculates overall distance for route from start to end in
        kilometers.

        :arg raw_route: raw route data retreived from db with pgrouting
        :type raw_route: list

        :arg colnames: list of column names retreived from db with pgrouting
        :type colnames: list

        :returns: route length
        :rtype: float

        """
        length = 0

        for segment in raw_route:
            length += segment[colnames.index('length')]

        return length

    def create_multiline_from_linesegments(self, raw_route, colnames):
        """Creates multiline ogr geometry from raw pgrouting route.

        .. note:: Raw pgrouting route consists of separate line segments.

        :arg raw_route: raw route data retreived from db with pgrouting
        :type raw_route: list

        :arg colnames: list of column names retreived from db with pgrouting
        :type colnames: list

        :returns: ogr multiline geometry representing route
        :rtype: osgeo.ogr.Geometry

        """
        multiline = ogr.Geometry(ogr.wkbMultiLineString)

        for segment in raw_route:
            the_geom = segment[colnames.index('the_geom')]
            line = ogr.CreateGeometryFromJson(the_geom)
            multiline.AddGeometry(line)

        return multiline
