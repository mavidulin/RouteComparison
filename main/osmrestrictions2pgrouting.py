# -*- coding: utf-8 -*-

# This script may take few minutes to execute because osm files are large.
# Be patient :)

import json
import psycopg2
import xml.etree.ElementTree as ET


class RestrictionProcessor(object):
    """
    RestrictionProcessor creates table that will store restrictions data,
    finds all restrictions for each way/relation in osm file, and saves
    restrictions to database.

    :arg connection: psycopg2 connection for database
    :type connection: psycopg2._psycopg.connection

    :arg xml_source_filename: name of file with osm data, e.g. croatia.osm
    :type xml_source_filename: string

    """

    def __init__(self, connection, xml_source_filename):
        self.restrictions_table = 'restrictions'
        self.connection = connection
        self.cursor = connection.cursor()
        self.xml_source = '../input_data/' + xml_source_filename

        self.run()

    def run(self):
        """
        This function creates table for restrictions if needed, loops through
        all elements in osm file and executes processing of element if it's
        type is 'relation'.
        """

        # Check if restrictions table exists.
        self.cursor.execute(
            """ SELECT EXISTS(
                SELECT * FROM information_schema.tables
                WHERE table_name=%s);
            """,
            (self.restrictions_table,)
        )
        restrictions_exists = self.cursor.fetchone()[0]

        # If restrictions table doesn't exist then create it.
        if not restrictions_exists:
            # Compose query... table_name must be set with format because when
            # setting it in execute() it is appended as 'string' which is
            # rejected by psycopg2.
            # All fields except 'restriction' are required.
            # 'Restriction' field is just for help.
            query = """ CREATE TABLE {table_name} (
                    rid serial,
                    to_cost double precision,
                    to_edge integer,
                    from_edge integer,
                    via text,
                    restriction text);
                """.format(table_name=self.restrictions_table)

            self.cursor.execute(query)
            self.connection.commit()

        # Get an iterable from xml file.
        context = ET.iterparse(self.xml_source, events=("start", "end"))

        # Turn context into an iterator.
        context = iter(context)

        # Get the root element of context.
        event, root = context.next()

        # Loop throught each element in xml file.
        for event, elem in context:
            if event == "end":
                if elem.tag == "relation":
                    self.process_relation(elem)

                root.clear()

        # Close DB connection.
        self.cursor.close()
        self.connection.close()

    def process_relation(self, relation):
        """
        This function finds all the members included in a restriction, sets cost
        parameter and executes a function that saves the restriction to the database.

        :arg relation: relation element from osm data
        :type relation: xml.etree.ElementTree.Element

        """
        # Find all 'tag' elements inside 'relation'.
        relation_tags = relation.findall('tag')

        for tag in relation_tags:
            if tag.attrib['k'] == 'restriction':
                print 'Found restriction ' + tag.attrib['v'] + '.'

                # Define dictionary for storing restriction members. It will
                # look like {'to': '4565', 'from': '55556', 'via': '55887'}.
                # Values in dict are ids from osm file.
                role_dict = {}

                members = relation.findall('member')

                for member in members:
                    # Member must be 'way'. Members also have type 'node'...
                    if member.attrib['type'] == 'way':
                        role_dict[member.attrib['role']] = member.attrib['ref']

                # Check if role_dict contains obligatory keys 'to' and 'from'.
                if 'to' in role_dict and 'from' in role_dict:
                    # Check which kind of restriction we have and set cost.
                    if tag.attrib['v'].startswith('only_'):
                        cost = 0.000001
                    elif tag.attrib['v'].startswith('no_'):
                        cost = 100000

                    # Find edges in 'ways' table that are related with "to",
                    # "from" and "via" edges by osm_id. For one edge in XML
                    # there can be many edges in ways table...
                    # Example result: [(123,), (124,)].
                    self.cursor.execute(
                        """SELECT gid FROM ways WHERE osm_id=%s """,
                        (role_dict['to'],)
                    )
                    to_edges = self.cursor.fetchall()

                    if to_edges:
                        # We only need first edge. ASSUMPTION!
                        to_edge = to_edges[0][0]
                    else:
                        to_edge = None

                    self.cursor.execute(
                        """SELECT gid FROM ways WHERE osm_id=%s """,
                        (role_dict['from'],)
                    )
                    from_edges = self.cursor.fetchall()

                    if from_edges:
                        # We only need last edge.ASSUMPTION!
                        from_edge = from_edges[-1][0]
                    else:
                        from_edge = None

                    if 'via' in role_dict:
                        self.cursor.execute(
                            """SELECT gid FROM ways WHERE osm_id=%s """,
                            (role_dict['via'],)
                        )
                        via_edges = self.cursor.fetchall()

                        if via_edges:
                            # We only need first edge. ASSUMPTION!
                            via = via_edges[0][0]
                        else:
                            via = None

                    # Execute Insert into restrictions.
                    if 'via' in role_dict:
                        self.insert_restrictions_with_via(
                            to_cost=cost,
                            to_edge=to_edge,
                            from_edge=from_edge,
                            via=via,
                            restriction=tag.attrib['v']
                        )
                    else:
                        self.insert_restrictions_no_via(
                            to_cost=cost,
                            to_edge=to_edge,
                            from_edge=from_edge,
                            restriction=tag.attrib['v']
                        )

                    # commit insertion
                    self.connection.commit()

    def insert_restrictions_with_via(
            self, to_cost, to_edge, from_edge, via, restriction):
        """Inserts new restriction into restriction table. It is important that
        besides other columns it inserts also 'via'.

        :arg to_cost: cost value for the restriction
        :type to_cost: float

        :arg to_edge: ending edge/way of the restriction
        :type to_edge: integer

        :arg from_edge: starting edge/way for the restriction
        :type from_edge: integer

        :arg via: edge/way that connects starting and ending edge/way of the
            restriction, e.g. 'no left turn from way 1 to way 3 via way 2'
        :type via: integer

        :arg restriction: Description/name of the restriction. It's not crucial
            for later route calculations but we use it as visual helper.
        :type restriction: string

        """
        # Compose query... table_name must be set with format because when
        # setting it in execute() it is appended as 'string' which is rejected
        # by psycopg2.
        query = """INSERT INTO {table_name} (
                to_cost,
                to_edge,
                from_edge,
                via,
                restriction)
                VALUES (%s, %s, %s, %s, %s);
            """.format(table_name=self.restrictions_table)

        self.cursor.execute(
            query,
            (to_cost, to_edge, from_edge, via, restriction)
        )

    def insert_restrictions_no_via(
            self, to_cost, to_edge, from_edge, restriction):
        """Inserts new restriction into restriction table.

        :arg to_cost: cost value for the restriction
        :type to_cost: float

        :arg to_edge: ending edge/way of the restriction
        :type to_edge: integer

        :arg from_edge: starting edge/way for the restriction
        :type from_edge: integer

        :arg restriction: Description/name of the restriction. It's not crucial
            for later route calculations but we use it as visual helper.
        :type restriction: string

        """
        # Compose query... table_name must be set with format because when
        # setting it in execute() it is appended as 'string' which is rejected
        # by psycopg2.
        query = """INSERT INTO {table_name} (
                to_cost,
                to_edge,
                from_edge,
                restriction)
                VALUES (%s, %s, %s, %s);
            """.format(table_name=self.restrictions_table)

        self.cursor.execute(
            query,
            (to_cost, to_edge, from_edge, restriction)
        )


if __name__ == '__main__':
    config_file = open('config.txt', 'r')
    config_content = config_file.read()
    config = json.loads(config_content)

    xml_source_filename = config['osm_source_filename']

    connection = psycopg2.connect(
        database=config['database']['name'],
        user=config['database']['user'],
        password=config['database']['password'],
        host=config['database']['host']
    )

    RestrictionProcessor(
        connection=connection,
        xml_source_filename=xml_source_filename
    )
