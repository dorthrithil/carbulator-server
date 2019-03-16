import datetime

from flask_restful import fields
from sqlalchemy import desc

from src.app import db
from src.models.debt import DebtModel
from src.models.refuel import RefuelModel
from src.models.tour import TourModel


class PayoffModel(db.Model):
    __tablename__ = 'payoffs'

    id = db.Column(db.Integer, primary_key=True)
    is_settled = db.Column(db.Boolean, default=False)
    time_created = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    time_updated = db.Column(db.DateTime(), onupdate=datetime.datetime.utcnow)
    debts = db.relationship("DebtModel")
    refuels = db.relationship("RefuelModel")
    tours = db.relationship("TourModel")
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
            'debts': fields.Nested(DebtModel.get_marshaller()),
            'tours': fields.Nested(TourModel.get_marshaller()),
            'refuels': fields.Nested(RefuelModel.get_marshaller()),
            'is_settled': fields.Boolean
        }

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id).all()

    @classmethod
    def find_latest_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id).order_by(desc(PayoffModel.time_created)).first()
