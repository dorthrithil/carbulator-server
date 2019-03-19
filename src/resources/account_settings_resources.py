from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, abort, reqparse

from src.messages.messages import USER_DOESNT_EXIST
from src.models.acount_settings import AccountSettingsModel
from src.models.user import UserModel

parser = reqparse.RequestParser()
parser.add_argument('auto_load_parking_place_gps_location', help='This field cannot be blank', required=True, type=bool)
parser.add_argument('parking_place_required', help='This field cannot be blank', required=True, type=bool)


class GetAccountSettings(Resource):

    @jwt_required
    @marshal_with(AccountSettingsModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())
        account_settings = AccountSettingsModel.find_by_user_id(user.id)
        if not account_settings:
            abort(404, message=USER_DOESNT_EXIST)
        return account_settings, 200


class UpdateAccountSettings(Resource):

    @jwt_required
    @marshal_with(AccountSettingsModel.get_marshaller())
    def put(self):
        data = parser.parse_args()

        user = UserModel.find_by_username(get_jwt_identity())
        account_settings = AccountSettingsModel.find_by_user_id(user.id)
        if not account_settings:
            abort(404, message=USER_DOESNT_EXIST)

        account_settings.auto_load_parking_place_gps_location = data['auto_load_parking_place_gps_location']
        account_settings.parking_place_required = data['parking_place_required']
        account_settings.persist()

        return account_settings, 200
