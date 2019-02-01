import datetime

from flask_restful import fields

from src.app import db
from src.exceptions.no_data import NoData
from src.models.community import CommunityModel
from src.models.user import UserModel


class TourModel(db.Model):
    __tablename__ = 'tours'

    id = db.Column(db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    time_updated = db.Column(db.DateTime(), onupdate=datetime.datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('UserModel', foreign_keys=[owner_id])
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    community = db.relationship('CommunityModel')
    start_km = db.Column(db.DECIMAL(precision=(10, 1)), nullable=False)
    end_km = db.Column(db.DECIMAL(precision=(10, 1)))
    start_time = db.Column(db.DateTime(), nullable=False)
    end_time = db.Column(db.DateTime())
    parking_position = db.Column(db.String(120))
    comment = db.Column(db.String(120))
    is_force_finished = db.Column(db.Boolean)
    force_finished_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    force_finished_by = db.relationship('UserModel', foreign_keys=[force_finished_by_id])
    payoff_id = db.Column(db.Integer, db.ForeignKey('payoffs.id'))
    is_open = db.Column(db.Boolean, default=True)
    passengers = db.relationship('UserModel', secondary='tour_passenger_link')

    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'id': fields.Integer,
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime,
            'start_time': fields.DateTime,
            'end_time': fields.DateTime,
            'owner': fields.Nested(UserModel.get_marshaller()),
            'community': fields.Nested(CommunityModel.get_marshaller()),
            'start_km': fields.String,
            'end_km': fields.String,
            'parking_position': fields.String,
            'comment': fields.String,
            'is_force_finished': fields.Boolean,
            'force_finished_by': fields.Nested(UserModel.get_marshaller(), allow_null=True),
            'is_open': fields.Boolean,
            'passengers': fields.Nested(UserModel.get_marshaller())
        }

    @classmethod
    def delete_by_id(cls, id):
        tour = db.session.query(cls).filter(cls.id == id).first()
        if tour:
            db.session.delete(tour)
            db.session.commit()
        else:
            raise NoData

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_finished_by_community(cls, community_id):
        return cls.query \
            .filter_by(community_id=community_id) \
            .filter(TourModel.end_km.isnot(None)) \
            .order_by(TourModel.end_time.desc()) \
            .all()

    @classmethod
    def find_finished_and_open_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id, is_open=True).filter(TourModel.end_km.isnot(None)).all()

    @classmethod
    def find_finished_by_user(cls, user_id):
        return cls.query.filter_by(owner_id=user_id).filter(TourModel.end_km.isnot(None)).all()

    @classmethod
    def find_running_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id).filter(TourModel.end_km.is_(None)).all()

    @classmethod
    def find_running_by_user(cls, user_id):
        return cls.query.filter_by(owner_id=user_id).filter(TourModel.end_km.is_(None)).all()

    @classmethod
    def find_newest_tour_for_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id).order_by(TourModel.end_km.desc()).first()
