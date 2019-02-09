from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, reqparse, abort

from src.exceptions.no_data import NoData
from src.messages.marshalling_objects import SimpleMessage
from src.messages.messages import INTERNAL_SERVER_ERROR, COMMUNIY_DOESNT_EXIST, UNAUTHORIZED, REFUEL_DELETED, \
    REFUEL_DOESNT_EXIST, CANT_CHANGE_REFUEL_COMMUNITY, CANNOT_DELETE_A_REFUEL_THAT_IS_PART_OF_A_PAYOFF
from src.models.community import CommunityModel
from src.models.refuel import RefuelModel
from src.models.user import UserModel
from src.util.parser_types import float_or_null

parser = reqparse.RequestParser()
parser.add_argument('costs', help='This field cannot be blank', required=True, type=float)
parser.add_argument('liters', required=False, type=float_or_null)
parser.add_argument('gas_station_name', required=False, type=str)


class SingleRefuel(Resource):

    @jwt_required
    @marshal_with(RefuelModel.get_marshaller())
    def get(self, community_id, id):
        user = UserModel.find_by_username(get_jwt_identity())
        refuel = RefuelModel.find_by_id(id)

        if not refuel:
            abort(404, message=REFUEL_DOESNT_EXIST)

        if user.id not in [u.id for u in refuel.community.users]:
            abort(401, message=UNAUTHORIZED)

        return refuel, 200

    @jwt_required
    @marshal_with(RefuelModel.get_marshaller())
    def put(self, community_id, id):
        data = parser.parse_args()

        refuel = RefuelModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not refuel:
            abort(404, message=REFUEL_DOESNT_EXIST)

        if not user.id == refuel.owner.id:
            abort(401, message=UNAUTHORIZED)

        if not refuel.community.id == community_id:
            abort(400, message=CANT_CHANGE_REFUEL_COMMUNITY)

        refuel.costs = round(data['costs'], 2)
        refuel.liters = data['liters']
        refuel.gas_station_name = data['gas_station_name']
        refuel.persist()

        return refuel, 200

    @jwt_required
    @marshal_with(SimpleMessage.get_marshaller())
    def delete(self, community_id, id):

        refuel = RefuelModel.find_by_id(id)
        if not refuel:
            abort(404, message=REFUEL_DOESNT_EXIST)

        user = UserModel.find_by_username(get_jwt_identity())

        if not user.id == refuel.owner.id:
            abort(401, message=UNAUTHORIZED)

        if not refuel.is_open:
            abort(401, message=CANNOT_DELETE_A_REFUEL_THAT_IS_PART_OF_A_PAYOFF)

        try:
            RefuelModel.delete_by_id(id)
        except NoData:
            abort(404, message=REFUEL_DOESNT_EXIST)
        return SimpleMessage(REFUEL_DELETED), 200


class AllRefuels(Resource):

    @jwt_required
    @marshal_with(RefuelModel.get_marshaller())
    def post(self, community_id):
        data = parser.parse_args()

        owner = UserModel.find_by_username(get_jwt_identity())
        community: CommunityModel = CommunityModel.find_by_id(community_id)

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if owner.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        new_refuel = RefuelModel(
            owner=owner,
            community=community,
            costs=round(data['costs'], 2),
            liters=data['liters'],
            gas_station_name=data['gas_station_name'],
        )

        try:
            new_refuel.persist()
            return new_refuel, 201
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)

    @jwt_required
    @marshal_with(RefuelModel.get_marshaller())
    def get(self, community_id):

        user = UserModel.find_by_username(get_jwt_identity())
        community: CommunityModel = CommunityModel.find_by_id(community_id)

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if user.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        return RefuelModel.find_by_community(community.id), 200


class UserRefuels(Resource):

    @jwt_required
    @marshal_with(RefuelModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())

        return RefuelModel.find_by_user(user.id), 200
