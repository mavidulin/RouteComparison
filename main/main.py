# -*- coding: utf-8 -*-
import json
import os
import datetime
import psycopg2

from utility import Utility
from pgrouting import PgRouting
from google import Google
from mapquest import MapQuest
from routes_processor import RoutesProcessor

UTILITY = Utility()


class Main(object):
    """Main class for application.

    :arg connection: psycopg2 connection for database
    :type connection: psycopg2._psycopg.connection

    :arg output_dir: directory for saving output files
    :type output_dir: string

    """

    def __init__(self, connection, output_dir, config):
        self.connection = connection
        self.cursor = connection.cursor()
        self.output_dir = output_dir
        self.config = config

        self.PgRouting = PgRouting(cursor=self.cursor)
        self.Google = Google(config['google_api_key'])
        self.MapQuest = MapQuest(config['mapquest_api_key'])
        self.RoutesProcessor = RoutesProcessor()

        self.time_named_dir = self.create_execution_directory()
        self.run()

    def run(self):
        """Main application function. Reads input file with locations for
        routing, executes method that creates output directory for routes,
        executes functions for getting routes, executes functions for
        processing routes.
        """
        # Open and read input file with locations. File content looks like
        # [{"start": {"x": 15.5, "y": 45.5},"end": {"x": 16.5, "y": 43.5}}].
        locations_file = open('locations.txt', 'r')
        locations_file_content = locations_file.read()

        # Convert string to json
        locations_list = json.loads(locations_file_content)

        # For each location pair (start-end)...
        for route_number in range(len(locations_list)):
            foldername = self.create_route_directory(route_number)

            start_coords = locations_list[route_number]['start']
            end_coords = locations_list[route_number]['end']

            # String with starting coordinates for route, e.g. '45.5,15.5'
            start_coords_string = (
                str(start_coords['y']) + ', ' + str(start_coords['x'])
            )

            # String with ending coordinates for route, e.g. '43.5,16.5'
            end_coords_string = (
                str(end_coords['y']) + ', ' + str(end_coords['x'])
            )

            pgrouting_data = (
                self.PgRouting.get_route_data(
                    start_coords=start_coords,
                    end_coords=end_coords,
                )
            )

            mapquest_data = (
                self.MapQuest.get_route_data(
                    start_coords=start_coords_string,
                    end_coords=end_coords_string,
                )
            )

            google_data = (
                self.Google.get_route_data(
                    start_coords=start_coords_string,
                    end_coords=end_coords_string,
                )
            )

            self.RoutesProcessor.process_geometry(
                pgrouting_data=pgrouting_data,
                mapquest_data=mapquest_data,
                google_data=google_data,
                route_number=route_number,
                foldername=foldername
            )
            self.RoutesProcessor.process_attributes(
                pgrouting_data=pgrouting_data,
                mapquest_data=mapquest_data,
                google_data=google_data,
                route_number=route_number,
                foldername=foldername
            )

        # Close DB connection.
        self.cursor.close()
        self.connection.close()

    def create_route_directory(self, route_number):
        """Creates directory for specific route.

        :arg route_number: ordinal of start-end location pair in file
        :type route_number: integer

        :returns: name of created directory
        :rtype: string

        """
        # Create directory named by route number.
        route_directory = (
            self.time_named_dir +
            '/route_' + str(route_number)
        )
        os.mkdir(route_directory)

        return route_directory

    def create_execution_directory(self):
        """Creates directory for current execution. Directory is named by
        current time.

        :returns: name of created directory
        :rtype: string

        """
        datetime_now = datetime.datetime.now()

        # Create directory named by current time.
        time_named_dir = (
            self.output_dir +
            '/date_' + str(datetime_now.day) + '_' + str(datetime_now.month) +
            '_' + str(datetime_now.year) + '_' + str(datetime_now.hour) + '_' +
            str(datetime_now.minute) + '_' + str(datetime_now.second)
        )
        os.mkdir(time_named_dir)

        return time_named_dir


if __name__ == '__main__':
    config_file = open('config.txt', 'r')
    config_content = config_file.read()
    config = json.loads(config_content)

    connection = psycopg2.connect(
        database=config['database']['name'],
        user=config['database']['user'],
        password=config['database']['password'],
        host=config['database']['host']
    )

    output_dir = os.path.abspath('../output_data')

    Main(connection=connection, output_dir=output_dir, config=config)
