from flask_jwt_extended import jwt_required
from flask_restful import Resource, marshal_with, abort

from src.exceptions.no_data import NoData
from src.messages.messages import NO_GEOCODING_RESULTS
from src.util.geocoding import GeocodingResult, geocode


class Geocode(Resource):

    @jwt_required
    @marshal_with(GeocodingResult.get_marshaller())
    def get(self, query):

        try:
            results = geocode(query)
            return results, 200
        except NoData:
            abort(404, message=NO_GEOCODING_RESULTS)
