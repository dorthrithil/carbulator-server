import pytz
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, abort

from src.messages.messages import COMMUNIY_DOESNT_EXIST, UNAUTHORIZED
from src.models.community import CommunityModel
from src.models.community_statistic import CommunityStatisticModel, KmPerUserModel
from src.models.tour import TourModel
from src.models.user import UserModel
from src.util.parser_types import moment


class GetCommunityStatistic(Resource):

    @jwt_required
    @marshal_with(CommunityStatisticModel.get_marshaller())
    def get(self, community_id, from_datetime, to_datetime):

        community: CommunityModel = CommunityModel.find_by_id(community_id)

        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        user = UserModel.find_by_username(get_jwt_identity())

        community_member_ids = [m.id for m in community.users]
        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        from_datetime = moment(from_datetime)
        to_datetime = moment(to_datetime)

        statistic = CommunityStatisticModel()
        statistic.community = community
        statistic.statistic_start = from_datetime
        statistic.statistic_end = to_datetime

        all_tours = TourModel.find_finished_by_community(community_id)
        km_per_user_dict = {}
        for user in community.users:
            km_per_user_dict[user.id] = KmPerUserModel()
            km_per_user_dict[user.id].user = user
            statistic.km_per_user.append(km_per_user_dict[user.id])
        for tour in all_tours:
            if from_datetime <= tour.end_time.astimezone(pytz.utc) <= to_datetime:
                km_per_user_dict[tour.owner_id].km += tour.end_km - tour.start_km

        return statistic, 200
