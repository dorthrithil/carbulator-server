import datetime

from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, reqparse, abort

from src.exceptions.no_data import NoData
from src.messages.marshalling import SimpleMessage
from src.messages.messages import INTERNAL_SERVER_ERROR, COMMUNIY_DOESNT_EXIST, UNAUTHORIZED, \
    CANT_START_TOUR_WHEN_HAVING_UNFINISHED_TOURS_IN_COMMUNITY, TOUR_NOT_FOUND, TOUR_HAS_ALREADY_BEEN_FINISHED, \
    CANNOT_CHANGE_TOUR_END_KM_WHEN_ANOTHER_TOUR_ALREADY_STARTED, CANNOT_UPDATE_UNFINISHED_TOURS, \
    CANNOT_DELETE_TOUR_WHEN_A_NEW_TOUR_HAS_ALREADY_STARTED, TOUR_DELETED, \
    NO_TOUR_EXISTING
from src.models.community import CommunityModel
from src.models.tour import TourModel
from src.models.user import UserModel

parser = reqparse.RequestParser()
parser.add_argument('start_km', help='This field cannot be blank', required=True, type=float)
parser.add_argument('passengers', type=int, action='append')
parser.add_argument('end_km', type=float)
parser.add_argument('comment', type=str)
parser.add_argument('parking_position', type=str)

finish_tour_parser = reqparse.RequestParser()
finish_tour_parser.add_argument('end_km', required=True, type=float)
finish_tour_parser.add_argument('comment', type=str)
finish_tour_parser.add_argument('parking_position', type=str)

edit_tour_parser = reqparse.RequestParser()
edit_tour_parser.add_argument('end_km', required=True, type=float)
edit_tour_parser.add_argument('comment', type=str)
edit_tour_parser.add_argument('parking_position', type=str)


class FinishTour(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def put(self, community_id, id):
        data = finish_tour_parser.parse_args()

        tour = TourModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not tour:
            abort(404, message=TOUR_NOT_FOUND)

        if not user.id == tour.owner.id:
            abort(401, message=UNAUTHORIZED)

        if tour.end_km:
            abort(400, message=TOUR_HAS_ALREADY_BEEN_FINISHED)

        tour.end_time = datetime.datetime.now()
        tour.end_km = data['end_km']
        tour.comment = data['comment']
        tour.parking_position = data['parking_position']
        tour.persist()

        return tour, 200


class ForceFinishTour(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def put(self, community_id, id):
        data = finish_tour_parser.parse_args()

        tour = TourModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not tour:
            abort(404, message=TOUR_NOT_FOUND)

        if user.id == tour.owner.id:
            abort(401, message=UNAUTHORIZED)

        if user.id not in [u.id for u in tour.community.users]:
            abort(401, message=UNAUTHORIZED)

        if tour.end_km:
            abort(400, message=TOUR_HAS_ALREADY_BEEN_FINISHED)

        tour.end_time = datetime.datetime.now()
        tour.end_km = data['end_km']
        tour.comment = data['comment']
        tour.parking_position = data['parking_position']
        tour.is_force_finished = True
        tour.force_finished_by = user
        tour.persist()

        return tour, 200


class SingleTour(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def put(self, community_id, id):
        data = edit_tour_parser.parse_args()

        tour = TourModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not tour:
            abort(404, message=TOUR_NOT_FOUND)

        if not user.id == tour.owner.id:
            abort(401, message=UNAUTHORIZED)

        if not tour.end_km:
            abort(400, message=CANNOT_UPDATE_UNFINISHED_TOURS)

        tour.comment = data['comment']
        tour.parking_position = data['parking_position']

        running_tours = TourModel.find_running_by_community(community_id)
        if running_tours and data['end_km'] != tour.end_km:
            abort(400, message=CANNOT_CHANGE_TOUR_END_KM_WHEN_ANOTHER_TOUR_ALREADY_STARTED)
        else:
            tour.end_km = data['end_km']

        tour.persist()

        return tour, 200

    @jwt_required
    @marshal_with(SimpleMessage.get_marshaller())
    def delete(self, community_id, id):

        tour = TourModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not tour:
            abort(404, message=TOUR_NOT_FOUND)

        if not user.id == tour.owner.id:
            abort(401, message=UNAUTHORIZED)

        running_tours = TourModel.find_running_by_community(community_id)

        if running_tours and (len(running_tours) > 1 or running_tours[0].id != id):
            abort(400, message=CANNOT_DELETE_TOUR_WHEN_A_NEW_TOUR_HAS_ALREADY_STARTED)

        try:
            TourModel.delete_by_id(id)
        except NoData:
            abort(404, message=TOUR_NOT_FOUND)
        return SimpleMessage(TOUR_DELETED), 200

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def get(self, community_id, id):

        tour = TourModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not tour:
            abort(404, message=TOUR_NOT_FOUND)

        if user.id not in [u.id for u in tour.community.users]:
            abort(401, message=UNAUTHORIZED)

        return tour, 200


class AllTours(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def post(self, community_id):
        data = parser.parse_args()

        owner = UserModel.find_by_username(get_jwt_identity())
        community: CommunityModel = CommunityModel.find_by_id(community_id)

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if owner.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        if TourModel.find_running_by_community(community_id):
            abort(400, message=CANT_START_TOUR_WHEN_HAVING_UNFINISHED_TOURS_IN_COMMUNITY)

        new_tour = TourModel(
            owner=owner,
            community=community,
            start_time=datetime.datetime.now(),
            start_km=data['start_km'],
        )

        try:
            new_tour.persist()
            return new_tour, 201
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class CommunityTours(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def get(self, community_id):

        user = UserModel.find_by_username(get_jwt_identity())
        community = CommunityModel.find_by_id(community_id)

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if user.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        return TourModel.find_finished_by_community(community_id), 200


class RunningCommunityTours(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def get(self, community_id):

        user = UserModel.find_by_username(get_jwt_identity())
        community = CommunityModel.find_by_id(community_id)

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if user.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        return TourModel.find_running_by_community(community_id), 200


class UserTours(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())

        return TourModel.find_finished_by_user(user.id), 200


class LatestTour(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def get(self, community_id):
        user = UserModel.find_by_username(get_jwt_identity())
        community = CommunityModel.find_by_id(community_id)

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if user.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        tour = TourModel.find_newest_tour_for_community(community_id)

        if not tour:
            abort(400, message=NO_TOUR_EXISTING)

        return tour, 200


class RunningUserTours(Resource):

    @jwt_required
    @marshal_with(TourModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())

        return TourModel.find_running_by_user(user.id), 200
