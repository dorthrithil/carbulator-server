from flask_restful import fields

from src.app import db
from src.exceptions.no_data import NoData
from src.models.community import CommunityModel
from src.models.user import UserModel


class TaskModel(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('UserModel', foreign_keys=[owner_id])
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    community = db.relationship('CommunityModel')
    km_interval = db.Column(db.Integer, nullable=True)
    km_interval_start = db.Column(db.DECIMAL(precision=(10, 1), nullable=True))
    time_interval = db.Column(db.Interval, nullable=True)
    time_interval_start = db.Column(db.DateTime(timezone=True), nullable=True)
    name = db.Column(db.String(120))
    description = db.Column(db.String(120))

    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'id': fields.Integer,
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime,
            'time_interval_start': fields.DateTime,
            'time_interval': fields.String,
            'owner': fields.Nested(UserModel.get_marshaller()),
            'community': fields.Nested(CommunityModel.get_marshaller()),
            'name': fields.String,
            'comment': fields.String,
            'km_interval': fields.Integer,
            'km_interval_start': fields.Float,
        }

    @classmethod
    def delete_by_id(cls, id):
        task = db.session.query(cls).filter(cls.id == id).first()
        if task:
            db.session.delete(task)
            db.session.commit()
        else:
            raise NoData

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_community(cls, community_id):
        return cls.query \
            .filter_by(community_id=community_id) \
            .all()
