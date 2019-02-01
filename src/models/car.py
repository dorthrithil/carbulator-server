import datetime

from flask_restful import fields

from src.app import db
from src.exceptions.no_data import NoData
from src.models.user import UserModel


class CarModel(db.Model):
    __tablename__ = 'cars'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    make = db.Column(db.String(120), nullable=False)
    model = db.Column(db.String(120), nullable=False)
    time_created = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    time_updated = db.Column(db.DateTime(), onupdate=datetime.datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('UserModel', back_populates='cars')

    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'id': fields.Integer,
            'name': fields.String,
            'make': fields.String,
            'model': fields.String,
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime,
            'owner': fields.Nested(UserModel.get_marshaller())
        }

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def return_all(cls):
        return CarModel.query.all()

    @classmethod
    def return_all_for_user(cls, user_id):
        return CarModel.query.filter(cls.owner_id == user_id).all()

    @classmethod
    def delete_all(cls):
        db.session.query(cls).delete()
        db.session.commit()

    @classmethod
    def delete_by_id(cls, id):
        car = db.session.query(cls).filter(cls.id == id).first()
        if car:
            db.session.delete(car)
            db.session.commit()
        else:
            raise NoData
