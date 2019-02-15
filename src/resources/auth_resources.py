import re
from datetime import datetime
from uuid import uuid4

from flask_jwt_extended import (create_access_token, create_refresh_token, jwt_required, jwt_refresh_token_required,
                                get_jwt_identity, get_raw_jwt)
from flask_restful import Resource, reqparse, marshal_with, abort

from src.messages.marshalling_objects import SimpleMessage, AuthResponse
from src.messages.messages import USER_ALREADY_EXISTS, USER_CREATION_SUCCESS, INTERNAL_SERVER_ERROR, LOGIN_SUCCESS, \
    USER_DOESNT_EXIST, WRONG_CREDENTIALS, ACCESS_TOKEN_REVOKED, REFRESH_TOKEN_REVOKED, USERNAME_TOO_SHORT, \
    USERNAME_INVALID, PASSWORD_TOO_SHORT, EMAIL_INVALID, USER_NOT_FOUND, RESET_PASSWORD_MAIL_SENT, \
    RESET_PASSWORD_HASH_INVALID, PASSWORD_RESET
from src.models.acount_settings import AccountSettingsModel
from src.models.revoked_token import RevokedTokenModel
from src.models.user import UserModel
from src.util.email import send_forgot_password_email
from src.util.regexes import email_regex, username_regex


class UserRegistration(Resource):
    @marshal_with(AuthResponse.get_marshaller())
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='This field cannot be blank', required=True, type=str)
        parser.add_argument('password', help='This field cannot be blank', required=True, type=str)
        parser.add_argument('email', help='This field cannot be blank', required=True, type=str)
        data = parser.parse_args()

        if UserModel.find_by_username(data['username']):
            abort(409, message=USER_ALREADY_EXISTS)

        if len(data['username']) < 3:
            abort(400, message=USERNAME_TOO_SHORT)

        if not re.match(username_regex, data['username']):
            abort(400, message=USERNAME_INVALID)

        if not re.match(email_regex, data['email']):
            abort(400, message=EMAIL_INVALID)

        if len(data['password']) < 8:
            abort(400, message=PASSWORD_TOO_SHORT)

        new_user = UserModel(
            username=data['username'],
            password=UserModel.generate_hash(data['password']),
            email=data['email']
        )

        new_account_settings = AccountSettingsModel()

        try:
            new_user.persist()
            new_account_settings.user_id = new_user.id
            new_account_settings.persist()
            access_token = create_access_token(identity=data['username'])
            refresh_token = create_refresh_token(identity=data['username'])
            return AuthResponse(
                USER_CREATION_SUCCESS,
                new_user,
                access_token=access_token,
                refresh_token=refresh_token), 201
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class UserLogin(Resource):
    @marshal_with(AuthResponse.get_marshaller())
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', help='This field cannot be blank', required=True, type=str)
        parser.add_argument('password', help='This field cannot be blank', required=True, type=str)
        data = parser.parse_args()
        current_user = UserModel.find_by_username(data['username'])

        if not current_user:
            abort(400, message=USER_DOESNT_EXIST)

        if UserModel.verify_hash(data['password'], current_user.password):
            access_token = create_access_token(identity=data['username'])
            refresh_token = create_refresh_token(identity=data['username'])
            return AuthResponse(LOGIN_SUCCESS,
                                current_user,
                                access_token=access_token,
                                refresh_token=refresh_token), 202
        else:
            abort(400, message=WRONG_CREDENTIALS)


class UserLogoutAccess(Resource):
    @jwt_required
    @marshal_with(SimpleMessage.get_marshaller())
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.persist()
            return SimpleMessage(ACCESS_TOKEN_REVOKED), 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class UserLogoutRefresh(Resource):
    @jwt_refresh_token_required
    @marshal_with(SimpleMessage.get_marshaller())
    def post(self):
        jti = get_raw_jwt()['jti']
        try:
            revoked_token = RevokedTokenModel(jti=jti)
            revoked_token.persist()
            return SimpleMessage(REFRESH_TOKEN_REVOKED), 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class TokenRefresh(Resource):
    @jwt_refresh_token_required
    @marshal_with(AuthResponse.get_marshaller())
    def post(self):
        current_user = UserModel.find_by_username(get_jwt_identity())
        access_token = create_access_token(identity=current_user.username)
        return AuthResponse(LOGIN_SUCCESS, current_user, access_token=access_token), 200


class ForgotPassword(Resource):
    @marshal_with(SimpleMessage.get_marshaller())
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('identification', help='This field cannot be blank', required=True, type=str)
        data = parser.parse_args()
        user = UserModel.find_by_username(data['identification'])
        if not user:
            user = UserModel.find_by_email(data['identification'])
        if not user:
            abort(401, message=USER_NOT_FOUND)
        try:
            user.reset_password_hash = uuid4()
            user.reset_password_hash_created = datetime.now()
            user.persist()
            send_forgot_password_email(user)
            return SimpleMessage(RESET_PASSWORD_MAIL_SENT), 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class ResetPassword(Resource):
    @marshal_with(AuthResponse.get_marshaller())
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('resetPasswordHash', help='This field cannot be blank', required=True, type=str)
        parser.add_argument('newPassword', help='This field cannot be blank', required=True, type=str)
        data = parser.parse_args()
        user = UserModel.find_by_reset_password_hash(data['resetPasswordHash'])
        if not user:
            abort(401, message=RESET_PASSWORD_HASH_INVALID)
        now = datetime.now()
        hash_age = now - user.reset_password_hash_created
        # Hash must be younger then 24 hours
        if divmod(hash_age.total_seconds(), 60 * 60 * 24)[0] > 0.0:
            abort(401, message=RESET_PASSWORD_HASH_INVALID)
        if len(data['newPassword']) < 8:
            abort(400, message=PASSWORD_TOO_SHORT)
        user.password = UserModel.generate_hash(data['newPassword'])
        user.reset_password_hash = None
        user.reset_password_hash_created = None
        user.persist()
        access_token = create_access_token(identity=user.username)
        refresh_token = create_refresh_token(identity=user.username)
        return AuthResponse(PASSWORD_RESET,
                            user,
                            access_token=access_token,
                            refresh_token=refresh_token), 202
