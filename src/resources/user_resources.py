from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, reqparse, abort

from src.messages.marshalling_objects import SimpleMessage
from src.messages.messages import NO_COMMUNITY_ID_GIVEN, COMMUNIY_DOESNT_EXIST, UNAUTHORIZED, PASSWORD_CHANGED, \
    PASSWORD_TOO_SHORT, OLD_PASSWORD_INCORRECT
from src.models.community import CommunityModel
from src.models.community_user_link import CommunityUserLinkModel
from src.models.user import UserModel

parser = reqparse.RequestParser()
parser.add_argument('username', help='This field cannot be blank', required=True, type=str)

search_parser = reqparse.RequestParser()
search_parser.add_argument('q', help='This field cannot be blank', required=True, type=str, location='args')
search_parser.add_argument('community', type=int, location='args')
search_parser.add_argument('only-uninvited', type=bool, location='args')


class AllUsers(Resource):
    @jwt_required
    @marshal_with(UserModel.get_marshaller())
    def get(self):
        return UserModel.return_all(), 200


class UserSearch(Resource):
    @jwt_required
    @marshal_with(UserModel.get_marshaller())
    def get(self):
        data = search_parser.parse_args()
        username = get_jwt_identity()
        users = UserModel.search_by_username(data['q'], username)
        if not data['only-uninvited']:
            return users
        else:
            if not data['community']:
                abort(400, message=NO_COMMUNITY_ID_GIVEN)

            community = CommunityModel.find_by_id(data['community'])
            if not community:
                abort(404, message=COMMUNIY_DOESNT_EXIST)

            if username not in [u.username for u in community.users]:
                abort(401, message=UNAUTHORIZED)

            invitations = CommunityUserLinkModel.find_by_community(data['community'])
            return [u for u in users if u.id not in [i.user_id for i in invitations]]


class ChangePassword(Resource):
    @jwt_required
    @marshal_with(SimpleMessage.get_marshaller())
    def put(self):
        password_parser = reqparse.RequestParser()
        password_parser.add_argument('old_password', help='This field cannot be blank', required=True, type=str)
        password_parser.add_argument('new_password', help='This field cannot be blank', required=True, type=str)
        data = password_parser.parse_args()
        user = UserModel.find_by_username(get_jwt_identity())
        if UserModel.verify_hash(data['old_password'], user.password):
            if len(data['new_password']) < 8:
                abort(400, message=PASSWORD_TOO_SHORT)
            user.password = UserModel.generate_hash(data['new_password'])
            user.persist()
            return SimpleMessage(PASSWORD_CHANGED), 201
        else:
            abort(401, message=OLD_PASSWORD_INCORRECT)
