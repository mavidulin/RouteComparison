# -*- coding: utf-8 -*-
import json

from shapely import wkt as shapely_wkt
from shapely.geometry import LineString
from osgeo import ogr

from utility import Utility

UTILITY = Utility()


class MapQuest(object):
    """This class handles mapquest route."""

    def __init__(self, api_key):
        self.base_url = (
            'http://open.mapquestapi.com/directions/v2/route'
        )
        self.api_key = api_key

    def get_route_data(self, start_coords, end_coords):
        """Executes function for making request to mapquest api and receives
        route from mapquest. Converts route to shapely and ogr geometry,
        creates buffer around the route and extracts numerical attribute data
        like driving time and length.

        :arg start_coords: string with route starting location coordinates,
            e.g. '45.5,15.5'
        :type start_coords: string

        :arg end_coords: string with route ending location coordinates,
            e.g. '43.5,16.5'
        :type end_coords: string

        :returns: dictionary with mapquest route data
        :rtype: dictionary

        """
        # Key-Value dictionary with data for mapquest api request.
        input_dict = {
            "from": start_coords,
            "to": end_coords,
            "outFormat": "json",
            "routeType": "fastest",
            "timeType": 1,
            "enhancedNarrative": "false",
            "shapeFormat": "raw",
            "generalize": 0,
            "locale": "en_US",
            "unit": "k",  # km
            "drivingStyle": 2,  # Normal driving style
            "highwayEfficiency": 21.0  # Units are miles/gallon.
        }

        route_data = UTILITY.make_service_request(
            base_url=self.base_url,
            key=self.api_key,
            values=input_dict
        )

        route_json = json.loads(route_data)

        route_shapely, route_ogr = (
            self.create_linestring(route_json=route_json)
        )

        route_buffer_ogr = (
            UTILITY.create_route_buffer(route=route_ogr)
        )
        route_buffer_shapely = shapely_wkt.loads(
            route_buffer_ogr.ExportToWkt()
        )

        driving_time = {
            'sec': route_json['route']['time'],
            'hms': route_json['route']['formattedTime']
        }

        return {
            'route_ogr': route_ogr,
            'route_shapely': route_shapely,
            'route_buffer_ogr': route_buffer_ogr,
            'route_buffer_shapely': route_buffer_shapely,
            'driving_time': driving_time,
            'len': route_json['route']['distance'],
        }

    def create_linestring(self, route_json):
        """Converts original mapquest route coordinates to more suitable format
        for creating shapely and ogr geometry. Creates Shapely and Ogr
        LineString geometries from route coordinates.

        :arg route_json: dictionary with mapquest route data
        :type route_json: dictionary

        :returns: tuple consisted of route's shapely and ogr geometry
        :rtype: (shapely.geometry.linestring.LineString, osgeo.ogr.Geometry)

        """
        # List of coordinates [x, y, x, y..., x, y]
        coords_list = route_json['route']['shape']['shapePoints']

        # Create list with points [[x, y], [x, y]...]
        point_list = []

        point_list = ([coords_list[x:x + 2] for x in range(
            0, len(coords_list), 2)
        ])

        # Convert [[lat, lng], [lat, lng]..] TO [[lng, lat], [lng, lat]...]
        for point in point_list:
            point.reverse()

        # Create shapely linestring from list of coordinate pairs.
        route_linestring_shapely = LineString(point_list)

        # Create ogr linestring.
        route_linestring_ogr = ogr.CreateGeometryFromWkb(
            route_linestring_shapely.wkb)

        return (route_linestring_shapely, route_linestring_ogr)
