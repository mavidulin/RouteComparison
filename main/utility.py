# -*- coding: utf-8 -*-
import urllib2
import urllib

from osgeo import ogr, osr
import copy


class Utility(object):
    """This class contains methods that are used for different objects."""

    def create_route_buffer(self, route):
        """Creates buffer around provided route.

        .. warning:: Because of making a copy of ogr geometry it will throw
            errors to console, but it's okay.

        .. note:: For creating buffer route has to be cloned first, then cloned
            route is transformed from epsg:4326 to epsg:3857 because we need
            geometry in metric units to be able to set buffer distance in
            meters. After buffer is created it has to be transformed back to
            original crs (epsg: 4326).

        :arg route: ogr geometry representing route
        :type route: osgeo.ogr.geometry

        :returns: route buffer geometry
        :rtype: osgeo.ogr.geometry

        """
        # Clone route.
        route_clone = copy.copy(route)

        # Define 4326 CRS
        source = osr.SpatialReference()
        source.ImportFromEPSG(4326)

        # Define 3857 CRS
        target = osr.SpatialReference()
        target.ImportFromEPSG(3857)

        # Define transformation way (from source to target)
        transform = osr.CoordinateTransformation(source, target)

        # Transform route clone.
        route_clone.Transform(transform)

        # Set buffer distance in meters and create buffer around route clone.
        buffer_distance = 11
        route_buffer = route_clone.Buffer(buffer_distance)

        # Define transformation way (from target to source)
        transform = osr.CoordinateTransformation(target, source)

        # Transform route buffer back to original CRS.
        route_buffer.Transform(transform)

        return route_buffer

    def create_geojson_file(self, geom, geomtype, filename):
        """Create GeoJson file for provided geometry.

        :arg geom: ogr geometry instance from which geojson file is created
        :type geom: osgeo.ogr.Geometry

        :arg geomtype: identificator for type of ogr geometry,
            e.g. ogr.wkbPolygon = 3
        :type geomtype: integer

        :arg filename: name of geojson file
        :type filename: string

        """
        # Create output ogr Driver
        out_driver = ogr.GetDriverByName('GeoJSON')

        # Create GeoJSON output
        out_data_source = out_driver.CreateDataSource(filename + '.geojson')
        # Create layer in GeoJson
        out_layer = out_data_source.CreateLayer(
            filename + '.geojson',
            geom_type=geomtype)

        # Get the output Layer's Feature Definition
        feature_defn = out_layer.GetLayerDefn()

        # Create a new feature
        out_feature = ogr.Feature(feature_defn)

        # Set new geometry for the feature
        out_feature.SetGeometry(geom)

        # Add new feature to output Layer
        out_layer.CreateFeature(out_feature)

        # destroy the feature
        out_feature.Destroy

        # Close DataSources
        out_data_source.Destroy()

    def make_service_request(self, base_url, key, values):
        """This function composes url for third-party services apis
        and sends request to the services defined by base_url param.
        For example, requests could be sent to Google and MapQuest apis.

        :arg base_url: base service url,
            e.g. http://open.mapquestapi.com/directions/v2/route
        :type base_url: string

        :arg key: user api key for service
        :type key: string

        :arg values: dictonary with parameters for service api
        :type values: dictionary

        :returns: service response data
        :rtype: string

        """
        # Encode values dict. {"one": 1, "two": 2} --> ?one=1&two=2
        url_values = urllib.urlencode(values)

        # When creating full_url add key separately because urllib.urlencode()
        # messes up (special) characters in key
        full_url = base_url + '?' + 'key=' + key + '&' + url_values

        response = urllib2.urlopen(full_url)

        response_data = response.read()

        return response_data
