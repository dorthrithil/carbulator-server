from typing import List

import geocoder
from flask_restful import fields

from src.exceptions.no_data import NoData


class GeocodingResult:
    """
    A class that holds geocoding results.
    """

    @staticmethod
    def get_marshaller():
        """
        Returns a marshaller for GeocodingResults.
        :return: GeocodingResult marshalling function.
        """
        return {
            'lat': fields.String,
            'lng': fields.String,
            'address': fields.String,
            'country': fields.String,
            'county': fields.String,
            'country_code': fields.String,
            'state': fields.String,
            'house_number': fields.String,
            'postal': fields.String,
            'town': fields.String,
            'type': fields.String,
            'street': fields.String,
        }

    @classmethod
    def from_osm_result(cls, osm_result):
        """
        Parses a osm geocoding result into the GeocodingResult class format.
        :param osm_result:
        :return: GeocodingResult.
        """
        geocoding_result = cls()
        geocoding_result.address = osm_result.get('address')
        geocoding_result.lat = osm_result.get('lat')
        geocoding_result.lng = osm_result.get('lng')
        geocoding_result.country = osm_result.get('country')
        geocoding_result.country_code = osm_result.get('country_code')
        geocoding_result.state = osm_result.get('state')
        geocoding_result.house_number = osm_result.get('housenumber')
        geocoding_result.postal = osm_result.get('postal')
        geocoding_result.county = osm_result.get('county')
        geocoding_result.town = osm_result.get('town')
        geocoding_result.type = osm_result.get('type')
        geocoding_result.street = osm_result.get('raw').get('address').get('pedestrian')
        return geocoding_result


def geocode_osm(query, max_rows):
    """
    Uses the OSM geooing tool to query Nominatim for results of the geocoding query.
    :param query: Query to geocode.
    :param max_rows: Max number of rows to fetch.
    :return: Raw osm geocoding result.
    """
    return geocoder.osm(query, max_rows=max_rows)


def geocode(query) -> List[GeocodingResult]:
    """
    Generic geocoding function. In case the geocoding provider needs to be switched for some reason, this can easily
    be done here.
    :param query: Query to geocode.
    :return: GeocodingResult.
    """
    osm_result = geocode_osm(query, 5)

    if not osm_result:
        raise NoData()

    results = []
    for osm_result_row in osm_result:
        results.append(GeocodingResult.from_osm_result(osm_result_row.json))

    return results
