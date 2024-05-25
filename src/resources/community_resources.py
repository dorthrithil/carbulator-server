from typing import List

from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, reqparse, abort

from src.app import db
from src.exceptions.no_data import NoData
from src.messages.marshalling_objects import SimpleMessage
from src.messages.messages import INTERNAL_SERVER_ERROR, COMMUNIY_WITH_THIS_CAR_ALREADY_EXISTS, COMMUNIY_DOESNT_EXIST, \
    COMMUNIY_DELETED, COMMUNIY_INVITATION_SENT, UNAUTHORIZED_TO_ACCEPT_COMMUNITY_INVITATION, \
    COMMUNITY_INVITATION_ALREADY_ACCEPTED, COMMUNITY_INVITATION_DOESNT_EXIST, COMMUNITY_INVITATION_ACCEPTED, \
    CAR_DOESNT_EXIST, USER_DOESNT_EXIST, USER_ALREADY_INVITED, NOT_AUTHORIZED_TO_REMOVE_USER_FROM_COMMUNITY, \
    COMMUNIY_LEFT_SUCCESSFULLY, COMMUNITY_INVITATION_DECLINED, UNAUTHORIZED, CANNOT_CREATE_COMMUNITY_WITH_FOREIGN_CAR, \
    COMMUNIY_LEFT_AND_DELETED, COMMUNITY_MARKED_AS_FAVOURITE, NO_FAVOURITE_COMMUNITY_FOUND
from src.models.car import CarModel
from src.models.community import CommunityModel
from src.models.community_user_link import CommunityUserLinkModel
from src.models.user import UserModel

post_parser = reqparse.RequestParser()
post_parser.add_argument('car', help='This field cannot be blank', required=True, type=int)
post_parser.add_argument('name', help='This field cannot be blank', required=True, type=str)

put_parser = reqparse.RequestParser()
put_parser.add_argument('name', help='This field cannot be blank', required=True, type=str)

invitation_parser = reqparse.RequestParser()
invitation_parser.add_argument('community', help='This field cannot be blank', required=True, type=int)
invitation_parser.add_argument('user', help='This field cannot be blank', required=True, type=str)


def assure_favourite_community(user_id):
    if CommunityUserLinkModel.find_favourite_by_user(user_id):
        return
    communities: List[CommunityUserLinkModel] = CommunityUserLinkModel.find_by_user(user_id)
    communities[0].is_favourite = True
    communities[0].persist()
    return communities[0]


class AllCommunityInvitations(Resource):

    @jwt_required()
    @marshal_with(SimpleMessage.get_marshaller())
    def post(self):
        data = invitation_parser.parse_args()

        user = UserModel.find_by_username(data['user'])
        community = CommunityModel.find_by_id(data['community'])

        if not user:
            abort(404, message=USER_DOESNT_EXIST)

        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        if user in community.users:
            abort(400, message=USER_ALREADY_INVITED)

        new_community_user_link = CommunityUserLinkModel(
            user_id=user.id,
            community_id=community.id,
            invitation_accepted=False,
            is_owner=False
        )

        try:
            new_community_user_link.persist()
            return SimpleMessage(COMMUNIY_INVITATION_SENT), 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class OpenCommunityInvitationsForUser(Resource):

    @jwt_required()
    @marshal_with(CommunityUserLinkModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())
        return CommunityUserLinkModel.find_open_invitations_by_user(user.id), 200


class InvitedUsers(Resource):

    @jwt_required()
    @marshal_with(UserModel.get_marshaller())
    def get(self, community_id: int):

        user = UserModel.find_by_username(get_jwt_identity())
        community = CommunityModel.find_by_id(community_id)

        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        if user not in community.users:
            abort(401, message=UNAUTHORIZED)

        invitations = CommunityUserLinkModel.find_open_invitations_by_community(community_id)
        return [i.user for i in invitations], 200


class SingleCommunityInvitation(Resource):

    @jwt_required()
    @marshal_with(SimpleMessage.get_marshaller())
    def put(self, community_id):
        user = UserModel.find_by_username(get_jwt_identity())
        invitation = CommunityUserLinkModel.find_by_user_and_community(user.id, community_id)

        if not invitation:
            abort(404, message=COMMUNITY_INVITATION_DOESNT_EXIST)

        if invitation.invitation_accepted:
            abort(400, message=COMMUNITY_INVITATION_ALREADY_ACCEPTED)

        if invitation.user_id != user.id:
            abort(401, message=UNAUTHORIZED_TO_ACCEPT_COMMUNITY_INVITATION)

        invitation.invitation_accepted = True
        invitation.persist()
        assure_favourite_community(user.id)

        return SimpleMessage(COMMUNITY_INVITATION_ACCEPTED), 200

    @jwt_required()
    @marshal_with(SimpleMessage.get_marshaller())
    def delete(self, community_id):
        user = UserModel.find_by_username(get_jwt_identity())
        invitation = CommunityUserLinkModel.find_by_user_and_community(user.id, community_id)

        if not invitation:
            abort(404, message=COMMUNITY_INVITATION_DOESNT_EXIST)

        if invitation.user_id != user.id:
            abort(401, message=NOT_AUTHORIZED_TO_REMOVE_USER_FROM_COMMUNITY)

        if invitation.invitation_accepted and not invitation.is_owner:
            invitation.delete()
            return SimpleMessage(COMMUNIY_LEFT_SUCCESSFULLY), 200

        if invitation.invitation_accepted and invitation.is_owner:
            CommunityModel.delete_by_id(invitation.community.id)
            return SimpleMessage(COMMUNIY_LEFT_AND_DELETED)

        invitation.delete()
        return SimpleMessage(COMMUNITY_INVITATION_DECLINED), 200


class SingleCommunity(Resource):

    @jwt_required()
    @marshal_with(CommunityModel.get_detailed_marshaller())
    def get(self, id):

        user = UserModel.find_by_username(get_jwt_identity())

        community = CommunityModel.find_by_id(id)
        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        if user not in community.users:
            abort(401, message=UNAUTHORIZED)

        is_owner = CommunityUserLinkModel.find_by_user_and_community(user.id, community.id).is_owner
        community.is_deletable = is_owner
        community.is_editable = is_owner

        return community, 200

    @jwt_required()
    @marshal_with(CommunityModel.get_marshaller())
    def put(self, id):
        data = put_parser.parse_args()

        community = CommunityModel.find_by_id(id)

        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        community.name = data['name']
        community.persist()

        return community, 200

    @jwt_required()
    @marshal_with(SimpleMessage.get_marshaller())
    def delete(self, id):
        user = UserModel.find_by_username(get_jwt_identity())

        try:
            link = CommunityUserLinkModel.find_by_user_and_community(user.id, id)
            if not link or not link.is_owner:
                abort(401, message=UNAUTHORIZED)
        except NoData:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        all_links = CommunityUserLinkModel.find_by_community(id)
        for link in all_links:
            link.delete()

        try:
            CommunityModel.delete_by_id(id)
        except NoData:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        return SimpleMessage(COMMUNIY_DELETED), 200


class AllCommunities(Resource):

    @jwt_required()
    @marshal_with(CommunityModel.add_is_fav_to_marshaller(CommunityModel.get_detailed_marshaller()))
    def post(self):
        data = post_parser.parse_args()

        founder = UserModel.find_by_username(get_jwt_identity())
        car = CarModel.find_by_id(data['car'])

        if not car:
            abort(404, message=CAR_DOESNT_EXIST)

        if not car.owner.id == founder.id:
            abort(400, message=CANNOT_CREATE_COMMUNITY_WITH_FOREIGN_CAR)

        if CommunityModel.find_by_car_id(car.id):
            abort(400, message=COMMUNIY_WITH_THIS_CAR_ALREADY_EXISTS)

        new_community = CommunityModel(
            name=data['name'],
            car=car,
            users=[founder]
        )

        try:
            new_community.persist()
            faved_community: CommunityUserLinkModel = assure_favourite_community(founder.id)
            if faved_community and faved_community.community_id == new_community.id:
                new_community.is_favourite = faved_community.is_favourite
            return new_community, 201
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class UserCommunities(Resource):

    @jwt_required()
    @marshal_with(CommunityModel.add_is_fav_to_marshaller(CommunityModel.get_detailed_marshaller()))
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())

        community_user_links = CommunityUserLinkModel.find_by_user(user.id)
        for cul in community_user_links:
            cul.community.is_favourite = cul.is_favourite

        user_communities = [c.community for c in community_user_links if c.invitation_accepted]

        for c in user_communities:
            is_owner = CommunityUserLinkModel.find_by_user_and_community(user.id, c.id).is_owner
            c.is_deletable = is_owner
            c.is_editable = is_owner

        return user_communities, 200


class CommunityUsers(Resource):

    @jwt_required()
    @marshal_with(UserModel.get_marshaller())
    def get(self, community_id):
        user = UserModel.find_by_username(get_jwt_identity())
        community = CommunityModel.find_by_id(community_id)

        if user not in community.users:
            abort(401, message=UNAUTHORIZED)

        return community.users, 200


class MarkCommunityAsFavourite(Resource):

    @jwt_required()
    @marshal_with(SimpleMessage.get_marshaller())
    def put(self, community_id):
        user = UserModel.find_by_username(get_jwt_identity())
        community_user_links = CommunityUserLinkModel.find_by_user(user.id)

        faved_community_cul = next((cul for cul in community_user_links if cul.community.id == community_id), None)

        if not faved_community_cul:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        if user not in faved_community_cul.community.users:
            abort(401, message=UNAUTHORIZED)

        try:
            for cul in community_user_links:
                cul.is_favourite = False
                cul.add_to_session()
            faved_community_cul.is_favourite = True
            faved_community_cul.add_to_session()
            db.session.commit()
            return SimpleMessage(COMMUNITY_MARKED_AS_FAVOURITE), 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class FavouriteCommunity(Resource):

    @jwt_required()
    @marshal_with(CommunityModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())
        cul = CommunityUserLinkModel.find_favourite_by_user(user.id)

        if not cul:
            abort(404, message=NO_FAVOURITE_COMMUNITY_FOUND)

        return cul.community, 200
