from datetime import datetime
from typing import List

from flask_restful import fields

from src.models.community import CommunityModel
from src.models.user import UserModel


class KmPerUserModel:
    user: UserModel
    km: float = 0
    km_accounted_for_passengers: float = 0

    @staticmethod
    def get_marshaller():
        return {
            'user': fields.Nested(UserModel.get_marshaller()),
            'km': fields.Float,
            'km_accounted_for_passengers': fields.Float
        }


class CommunityStatisticModel:
    community: CommunityModel
    statistic_start: datetime
    statistic_end: datetime
    km_per_user: List[KmPerUserModel] = []

    def __init__(self):
        self.km_per_user = []

    @staticmethod
    def get_marshaller():
        return {
            'community': fields.Nested(CommunityModel.get_marshaller()),
            'statistic_start': fields.DateTime,
            'statistic_end': fields.DateTime,
            'km_per_user': fields.Nested(KmPerUserModel.get_marshaller())
        }
