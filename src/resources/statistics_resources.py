import datetime

import pytz
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, abort

from src.messages.messages import COMMUNIY_DOESNT_EXIST, UNAUTHORIZED
from src.models.community import CommunityModel
from src.models.community_statistic import CommunityStatisticModel, KmPerUserModel, CostsPerUserModel
from src.models.payoff import PayoffModel
from src.models.refuel import RefuelModel
from src.models.tour import TourModel
from src.models.user import UserModel
from src.util.parser_types import moment


def get_community_statistic(community_id, from_datetime, to_datetime):
    community: CommunityModel = CommunityModel.find_by_id(community_id)

    if not community:
        abort(404, message=COMMUNIY_DOESNT_EXIST)

    user = UserModel.find_by_username(get_jwt_identity())

    community_member_ids = [m.id for m in community.users]
    if user.id not in community_member_ids:
        abort(401, message=UNAUTHORIZED)

    statistic = CommunityStatisticModel()
    statistic.community = community
    statistic.statistic_start = from_datetime
    statistic.statistic_end = to_datetime

    all_tours = TourModel.find_finished_by_community(community_id)
    all_costs = RefuelModel.find_by_community(community_id)
    km_per_user_dict = {}
    costs_per_user_dict = {}
    for user in community.users:
        km_per_user_dict[user.id] = KmPerUserModel()
        km_per_user_dict[user.id].user = user
        statistic.km_per_user.append(km_per_user_dict[user.id])
        costs_per_user_dict[user.id] = CostsPerUserModel()
        costs_per_user_dict[user.id].user = user
        statistic.costs_per_user.append(costs_per_user_dict[user.id])
    for tour in all_tours:
        if from_datetime <= tour.end_time.astimezone(pytz.utc) <= to_datetime:
            tour_km = tour.end_km - tour.start_km
            km_per_user_dict[tour.owner_id].km += tour_km
            # Divide km of passengers
            all_passengers_ids = [tour.owner_id] + [passenger.id for passenger in tour.passengers]
            for passenger_id in all_passengers_ids:
                km_per_user_dict[passenger_id].km_accounted_for_passengers += tour_km / len(all_passengers_ids)
    for cost in all_costs:
        if from_datetime <= cost.time_created.astimezone(pytz.utc) <= to_datetime:
            costs_per_user_dict[cost.owner_id].costs += cost.costs

    return statistic


class GetCommunityStatistic(Resource):

    @jwt_required()
    @marshal_with(CommunityStatisticModel.get_marshaller())
    def get(self, community_id, from_datetime, to_datetime):
        return get_community_statistic(community_id, moment(from_datetime), moment(to_datetime)), 200


class GetCommunityStatisticCurrentPayoffIntervall(Resource):

    @jwt_required()
    @marshal_with(CommunityStatisticModel.get_marshaller())
    def get(self, community_id):
        latest_payoff = PayoffModel.find_latest_by_community(community_id)

        if not latest_payoff:
            from_datetime = datetime.datetime.min.replace(year=2000).astimezone(pytz.utc)
        else:
            from_datetime = latest_payoff.time_created.astimezone(pytz.utc)
        to_datetime = datetime.datetime.now().astimezone(pytz.utc)

        return get_community_statistic(community_id, from_datetime, to_datetime), 200
