from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, reqparse, abort

from src.messages.marshalling_objects import SimpleMessage
from src.messages.messages import INTERNAL_SERVER_ERROR, COMMUNIY_DOESNT_EXIST, \
    UNAUTHORIZED, END_MUST_BE_AFTER_START, EVENT_DOESNT_EXIST, EVENT_DELETED, TO_MUST_BE_AFTER_FROM
from src.models.community import CommunityModel
from src.models.event import EventModel
from src.models.user import UserModel
from src.util.parser_types import moment

parser = reqparse.RequestParser()
parser.add_argument('title', help='This field cannot be blank', required=True, type=str)
parser.add_argument('description', type=str)
parser.add_argument('start', help='This field cannot be blank', required=True, type=moment)
parser.add_argument('end', help='This field cannot be blank', required=True, type=moment)


class CreateEvent(Resource):

    @jwt_required()
    @marshal_with(EventModel.get_marshaller())
    def post(self, community_id):
        data = parser.parse_args()

        owner = UserModel.find_by_username(get_jwt_identity())
        community: CommunityModel = CommunityModel.find_by_id(community_id)
        community_member_ids = [m.id for m in community.users]

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if owner.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        if not data['end'] > data['start']:
            abort(400, message=END_MUST_BE_AFTER_START)

        new_event = EventModel(
            owner=owner,
            title=data['title'],
            description=data['description'],
            start=data['start'],
            end=data['end'],
            community_id=community.id
        )

        try:
            new_event.persist()
            return new_event, 201
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class EditEvent(Resource):

    @jwt_required()
    @marshal_with(EventModel.get_marshaller())
    def put(self, event_id):
        data = parser.parse_args()

        owner = UserModel.find_by_username(get_jwt_identity())
        event: EventModel = EventModel.find_by_id(event_id)

        if not event:
            abort(400, message=EVENT_DOESNT_EXIST)

        if owner != event.owner:
            abort(401, message=UNAUTHORIZED)

        if not data['end'] > data['start']:
            abort(400, message=END_MUST_BE_AFTER_START)

        event.title = data['title']
        event.description = data['description']
        event.start = data['start']
        event.end = data['end']

        try:
            event.persist()
            return event, 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class GetEvent(Resource):

    @jwt_required()
    @marshal_with(EventModel.get_marshaller())
    def get(self, event_id):

        event: EventModel = EventModel.find_by_id(event_id)

        if not event:
            abort(404, message=EVENT_DOESNT_EXIST)

        community_member_ids = [m.id for m in event.community.users]
        user = UserModel.find_by_username(get_jwt_identity())

        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        return event, 200


class GetEvents(Resource):

    @jwt_required()
    @marshal_with(EventModel.get_marshaller())
    def get(self, community_id, from_datetime, to_datetime):

        owner = UserModel.find_by_username(get_jwt_identity())
        community: CommunityModel = CommunityModel.find_by_id(community_id)
        community_member_ids = [m.id for m in community.users]

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if owner.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        from_datetime = moment(from_datetime)
        to_datetime = moment(to_datetime)

        if not to_datetime > from_datetime:
            abort(400, message=TO_MUST_BE_AFTER_FROM)

        events: EventModel = EventModel.find_by_community(community_id, from_datetime, to_datetime)

        return events, 200


class GetNextEvents(Resource):

    @jwt_required()
    @marshal_with(EventModel.get_marshaller())
    def get(self, community_id, number_of_events):

        owner = UserModel.find_by_username(get_jwt_identity())
        community: CommunityModel = CommunityModel.find_by_id(community_id)
        community_member_ids = [m.id for m in community.users]

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if owner.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        events: EventModel = EventModel.find_next_n_by_community(community_id, number_of_events)

        return events, 200


class DeleteEvent(Resource):

    @jwt_required()
    @marshal_with(SimpleMessage.get_marshaller())
    def delete(self, event_id):

        event: EventModel = EventModel.find_by_id(event_id)

        if not event:
            abort(404, message=EVENT_DOESNT_EXIST)

        community_member_ids = [m.id for m in event.community.users]
        user = UserModel.find_by_username(get_jwt_identity())

        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        try:
            event.delete_by_id(event_id)
            return SimpleMessage(EVENT_DELETED), 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)
