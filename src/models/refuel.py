import datetime

from flask_restful import fields

from src.app import db
from src.exceptions.no_data import NoData
from src.models.user import UserModel


class RefuelModel(db.Model):
    __tablename__ = 'refuels'

    id = db.Column(db.Integer, primary_key=True)
    costs = db.Column(db.DECIMAL(10,2), nullable=False)
    liters = db.Column(db.DECIMAL(10,2))
    gas_station_name = db.Column(db.String(120))
    time_created = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    time_updated = db.Column(db.DateTime(), onupdate=datetime.datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('UserModel')
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    community = db.relationship('CommunityModel')
    payoff_id = db.Column(db.Integer, db.ForeignKey('payoffs.id'))
    is_open = db.Column(db.Boolean, default=True)

    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'id': fields.Integer,
            'costs': fields.Float,
            'liters': fields.Float,
            'gas_station_name': fields.String,
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime,
            'is_open': fields.Boolean,
            'owner': fields.Nested(UserModel.get_marshaller())
        }

    @classmethod
    def delete_by_id(cls, id):
        refuel = db.session.query(cls).filter(cls.id == id).first()
        if refuel:
            db.session.delete(refuel)
            db.session.commit()
        else:
            raise NoData

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id).order_by(RefuelModel.time_created.desc()).all()

    @classmethod
    def find_open_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id, is_open=True).all()

    @classmethod
    def find_by_user(cls, user_id):
        return cls.query.filter_by(owner_id=user_id).all()
