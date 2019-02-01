from flask_restful import fields

from src.app import db
from src.exceptions.no_data import NoData
from src.models.user import UserModel


class EventModel(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('UserModel', foreign_keys=[owner_id])
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    community = db.relationship('CommunityModel', foreign_keys=[community_id])
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start = db.Column(db.DateTime(timezone=True))
    end = db.Column(db.DateTime(timezone=True))

    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'id': fields.Integer,
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime,
            'owner': fields.Nested(UserModel.get_marshaller()),
            'title': fields.String,
            'description': fields.String,
            'start': fields.DateTime,
            'end': fields.DateTime,
        }

    @classmethod
    def delete_by_id(cls, event_id):
        event = db.session.query(cls).filter(cls.id == event_id).first()
        if event:
            db.session.delete(event)
            db.session.commit()
        else:
            raise NoData

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_community(cls, community_id, from_datetime, to_datetime):
        return cls.query.filter_by(community_id=community_id). \
            filter(EventModel.end >= from_datetime, EventModel.start <= to_datetime).all()
