# -*- coding: utf-8 -*-
import json
import datetime as DT

from shapely import wkt as shapely_wkt
from shapely.geometry import MultiLineString
from osgeo import ogr

# from google_polyline_decoder import decode_google_polyline
from google_polyline_decoder import GooglePolylineDecoder
from utility import Utility

UTILITY = Utility()
GOOGLE_POLYLINE_DECODER = GooglePolylineDecoder()


class Google(object):
    """This class handles google route."""

    def __init__(self, api_key):
        self.base_url = (
            'https://maps.googleapis.com/maps/api/directions/json'
        )
        self.api_key = api_key

    def get_route_data(self, start_coords, end_coords):
        """Executes function for making request to Google api and receives
        route from Google. Converts route to shapely and ogr geometry,
        creates buffer around the route and extracts numerical attribute data
        like driving time and length.

        .. warning:: LENGTH AND DRIVING TIME ARE NOT EXTRACTED!

        :arg start_coords: string with route starting location coordinates,
            e.g. '45.5,15.5'
        :type start_coords: string

        :arg end_coords: string with route ending location coordinates,
            e.g. '43.5,16.5'
        :type end_coords: string

        :returns: dictionary with google route data
        :rtype: dictionary

        """
        # Key-Value dictionary with data for google api request.
        input_dict = {
            "origin": start_coords,
            "destination": end_coords,
            "mode": "driving",
            "units": "metric",
        }

        route_data = UTILITY.make_service_request(
            base_url=self.base_url,
            key=self.api_key,
            values=input_dict
        )

        route_json = json.loads(route_data)

        route_shapely, route_ogr, route_distance, driving_time = (
            self.create_multilinestring(route_json=route_json)
        )

        route_buffer_ogr = UTILITY.create_route_buffer(route=route_ogr)
        route_buffer_shapely = shapely_wkt.loads(
            route_buffer_ogr.ExportToWkt()
        )

        return {
            'route_ogr': route_ogr,
            'route_shapely': route_shapely,
            'route_buffer_ogr': route_buffer_ogr,
            'route_buffer_shapely': route_buffer_shapely,
            'driving_time': driving_time,
            'len': route_distance,
        }

    def create_multilinestring(self, route_json):
        """Converts original google route data to more suitable format
        for creating shapely and ogr geometry. Creates Shapely and Ogr
        LineString geometries from route coordinates.

        .. note:: Raw Google route data is in proprietary format, so
            GOOGLE_POLYLINE_DECODER is needed to convert it to more suitable
            format. Moreover, Raw google data may contain multiple routes,
            each route contains legs, each leg contains steps and each step
            contains encoded polyline points.

        :arg route_json: dictionary with google route data
        :type route_json: dictionary

        :returns: tuple consisted of route's shapely and ogr geometry
        :rtype: (shapely.geometry.linestring.LineString, osgeo.ogr.Geometry)

        """
        # List of all polylines.
        polyline_list = []
        route_distance = 0
        duration = 0

        for route in route_json['routes']:
            for leg in route['legs']:
                route_distance += leg['distance']['value'] / 1000.0
                duration += leg['duration']['value']

                for step in leg['steps']:  # step is "edge"
                    decoded_polyline = (
                        GOOGLE_POLYLINE_DECODER.decode_google_polyline(
                            point_str=step['polyline']['points']
                        )
                    )

                    polyline_list.append(decoded_polyline)

        # Create shapely multilinestring from list of polylines.
        route_multilinestring_shapely = MultiLineString(polyline_list)
        # Create ogr multilinestring
        route_multilinestring_ogr = ogr.CreateGeometryFromWkb(
            route_multilinestring_shapely.wkb
        )

        driving_time = {
            'sec': duration,
            'hms': DT.timedelta(seconds=duration)
        }

        return (route_multilinestring_shapely,
                route_multilinestring_ogr,
                route_distance,
                driving_time)
