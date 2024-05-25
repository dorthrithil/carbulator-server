from collections import OrderedDict
from typing import List

import numpy as np
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, abort

from src.messages.messages import UNAUTHORIZED, CANT_CREATE_PAYOFF_WHEN_UNFINISHED_TOURS_EXIST, \
    CANT_CREATE_PAYOFF_WITHOUT_NEW_REFUELS_AND_TOURS, COMMUNIY_DOESNT_EXIST, PAYOFF_DOESNT_EXIST, DEBT_DOESNT_EXIST
from src.models.community import CommunityModel
from src.models.debt import DebtModel
from src.models.payoff import PayoffModel
from src.models.refuel import RefuelModel
from src.models.tour import TourModel
from src.models.user import UserModel
from src.util.simplify_debt_matrix import simplify_debt_matrix


class AllPayoffs(Resource):

    @jwt_required()
    @marshal_with(PayoffModel.get_marshaller())
    def post(self, id):
        community = CommunityModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        if user.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        if TourModel.find_running_by_community(id):
            abort(400, message=CANT_CREATE_PAYOFF_WHEN_UNFINISHED_TOURS_EXIST)

        # tours: List[TourModel] = TourModel.find_finished_and_open_by_community(id)
        # refuels: List[RefuelModel] = RefuelModel.find_open_by_community(id)
        tours: List[TourModel] = TourModel.find_finished_by_community(id)
        refuels: List[RefuelModel] = RefuelModel.find_by_community(id)

        if not [t for t in tours if t.is_open] and not [r for r in refuels if r.is_open]:
            abort(400, message=CANT_CREATE_PAYOFF_WITHOUT_NEW_REFUELS_AND_TOURS)

        # Calculate some basic statistics
        total_km = sum(map(lambda t: t.end_km - t.start_km, tours))
        km_per_user = {}
        for tour in tours:
            involved_users = [tour.owner] + tour.passengers
            km_per_involved_user = (tour.end_km - tour.start_km) / len(involved_users)
            for involved_user in involved_users:
                if involved_user.id not in km_per_user:
                    km_per_user[involved_user.id] = 0
                km_per_user[involved_user.id] += km_per_involved_user
        # If there is a user from refuels missing, he has zero costs/kms
        for refuel in refuels:
            if refuel.owner.id not in km_per_user:
                km_per_user[refuel.owner.id] = 0
        km_fraction_per_user = {}
        for user_id, km in km_per_user.items():
            km_fraction_per_user[user_id] = km / total_km

        # Create reference user id to user dict
        user_dictionary = OrderedDict()
        for tour in tours:
            if tour.owner.id not in user_dictionary:
                user_dictionary[tour.owner.id] = tour.owner
            for passenger in tour.passengers:
                if passenger.id not in user_dictionary:
                    user_dictionary[passenger.id] = passenger
        for refuel in refuels:
            if refuel.owner.id not in user_dictionary:
                user_dictionary[refuel.owner.id] = refuel.owner

        # Create debt matrix (debtee on y axis, recipient on x axis)
        debt_matrix = np.zeros((len(user_dictionary), len(user_dictionary)))
        for refuel in refuels:
            recipient_position = list(user_dictionary.keys()).index(refuel.owner.id)
            for user_id in user_dictionary.keys():
                if user_id != refuel.owner.id:
                    debtee_position = list(user_dictionary.keys()).index(user_id)
                    debt_amount = refuel.costs * km_fraction_per_user[user_id]
                    debt_matrix[debtee_position, recipient_position] += float(debt_amount)

        # Include already created debts from previous payoffs
        debts = DebtModel.find_by_community(id)
        for debt in debts:
            recipient_position = list(user_dictionary.keys()).index(debt.recepient_id)
            debtee_position = list(user_dictionary.keys()).index(debt.debtee_id)
            debt_matrix[debtee_position, recipient_position] -= float(debt.amount)

        # Simplify debt matrix
        debt_matrix = simplify_debt_matrix(debt_matrix)

        # Create and persist payoff
        payoff = PayoffModel()
        payoff.community_id = id
        payoff.persist()

        # Create and persist debt objects
        for i in range(debt_matrix.shape[0]):
            for j in range(debt_matrix.shape[0]):
                if debt_matrix[i, j] != 0:
                    debt = DebtModel()
                    debt.debtee = list(user_dictionary.values())[i]
                    debt.recepient = list(user_dictionary.values())[j]
                    debt.amount = round(debt_matrix[i, j], 2)
                    debt.payoff_id = payoff.id
                    debt.community_id = id
                    debt.persist()

        # If there is no resulting debt in the payoff, the payoff is settled
        if not np.any(debt_matrix != 0):
            payoff.is_settled = True

        # Set open tours to non open and add payoff id
        for tour in tours:
            if tour.is_open:
                tour.is_open = False
                tour.payoff_id = payoff.id
                tour.persist()

        # Set open refuels to non open and add payoff id
        for refuel in refuels:
            if refuel.is_open:
                refuel.is_open = False
                refuel.payoff_id = payoff.id
                refuel.persist()

        return payoff, 201

    @jwt_required()
    @marshal_with(PayoffModel.get_marshaller())
    def get(self, id):
        community = CommunityModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        if user.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        payoffs = PayoffModel.find_by_community(id)

        return payoffs, 200


class SinglePayoff(Resource):

    @jwt_required()
    @marshal_with(PayoffModel.get_marshaller())
    def get(self, id):

        payoff = PayoffModel.find_by_id(id)

        if not payoff:
            abort(404, message=PAYOFF_DOESNT_EXIST)

        community = CommunityModel.find_by_id(payoff.community_id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        if user.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        return payoff, 200


class CommunityDebts(Resource):

    @jwt_required()
    @marshal_with(DebtModel.get_marshaller())
    def get(self, id):
        community = CommunityModel.find_by_id(id)
        user = UserModel.find_by_username(get_jwt_identity())

        if not community:
            abort(404, message=COMMUNIY_DOESNT_EXIST)

        if user.id not in [u.id for u in community.users]:
            abort(401, message=UNAUTHORIZED)

        debts = DebtModel.find_unsettled_by_community(id)

        return debts, 200


class UserDebts(Resource):

    @jwt_required()
    @marshal_with(DebtModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())

        debts = DebtModel.find_unsettled_by_user(user.id)

        return debts, 200


class SettleDebt(Resource):

    @jwt_required()
    @marshal_with(DebtModel.get_marshaller())
    def put(self, id):
        user = UserModel.find_by_username(get_jwt_identity())
        debt = DebtModel.find_by_id(id)

        if not debt:
            abort(404, message=DEBT_DOESNT_EXIST)

        debt = DebtModel.find_by_id(id)

        if not (debt.recepient.id == user.id or debt.debtee.id == user.id):
            abort(401, message=UNAUTHORIZED)

        debt.is_settled = True
        debt.persist()

        payoff = PayoffModel.find_by_id(debt.payoff_id)
        remaining_debts = DebtModel.find_unsettled_by_payoff(payoff.id)
        if not remaining_debts:
            payoff.is_settled = True
            payoff.persist()

        return debt, 200


class UnsettleDebt(Resource):

    @jwt_required()
    @marshal_with(DebtModel.get_marshaller())
    def put(self, id):
        user = UserModel.find_by_username(get_jwt_identity())
        debt = DebtModel.find_by_id(id)

        if not debt:
            abort(404, message=DEBT_DOESNT_EXIST)

        debt = DebtModel.find_by_id(id)

        if not (debt.recepient.id == user.id or debt.debtee.id == user.id):
            abort(401, message=UNAUTHORIZED)

        debt.is_settled = False
        debt.persist()

        payoff = PayoffModel.find_by_id(debt.payoff_id)
        if payoff.is_settled:
            payoff.is_settled = False
            payoff.persist()

        return debt, 200
