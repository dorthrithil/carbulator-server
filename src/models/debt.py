import datetime

from flask_restful import fields

from src.app import db
from src.models.user import UserModel


class DebtModel(db.Model):
    __tablename__ = 'debts'

    id = db.Column(db.Integer, primary_key=True)
    is_settled = db.Column(db.Boolean, default=False)
    amount = db.Column(db.DECIMAL(10,2), nullable=False)
    time_created = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    time_updated = db.Column(db.DateTime(), onupdate=datetime.datetime.utcnow)
    debtee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    debtee = db.relationship('UserModel', foreign_keys=[debtee_id])
    recepient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recepient = db.relationship('UserModel', foreign_keys=[recepient_id])
    payoff_id = db.Column(db.Integer, db.ForeignKey('payoffs.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)

    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'id': fields.Integer,
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime,
            'debtee': fields.Nested(UserModel.get_marshaller()),
            'recepient': fields.Nested(UserModel.get_marshaller()),
            'is_settled': fields.Boolean,
            'amount': fields.Float
        }

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_unsettled_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id, is_settled=False).all()

    @classmethod
    def find_unsettled_by_user(cls, user_id):
        return cls.query.filter(((DebtModel.recepient_id == user_id) | (DebtModel.debtee_id == user_id)),
                                DebtModel.is_settled == False).all()

    @classmethod
    def find_unsettled_by_payoff(cls, payoff_id):
        return cls.query.filter_by(payoff_id=payoff_id, is_settled=False).all()
