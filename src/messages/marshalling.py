from flask_restful import fields

from src.models.user import UserModel


class SimpleMessage:

    def __init__(self, message: str):
        self.message = message

    @staticmethod
    def get_marshaller():
        return {
            'message': fields.String
        }


class AuthResponse:

    def __init__(self, message: str, user: UserModel, refresh_token: str = None, access_token: str = None):
        self.message = message
        self.user = user
        self.refresh_token = refresh_token
        self.access_token = access_token

    @staticmethod
    def get_marshaller():
        return {
            'message': fields.String,
            'access_token': fields.String,
            'refresh_token': fields.String,
            'user': fields.Nested(UserModel.get_marshaller())
        }
