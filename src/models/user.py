from flask_restful import fields
from passlib.hash import pbkdf2_sha256 as sha256

from src.app import db


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    time_created = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    cars = db.relationship("CarModel", back_populates="owner")
    communities = db.relationship("CommunityModel", secondary='community_user_link')
    tours = db.relationship("TourModel", secondary='tour_passenger_link')
    reset_password_hash = db.Column(db.String(120), nullable=True, default=None)
    reset_password_hash_created = db.Column(db.DateTime(timezone=True), default=None, nullable=True)

    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'id': fields.Integer,
            'username': fields.String,
            'email': fields.String,
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime
        }

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()

    @classmethod
    def find_by_reset_password_hash(cls, hash):
        return cls.query.filter_by(reset_password_hash=hash).first()

    @classmethod
    def return_all(cls):
        return UserModel.query.all()

    @classmethod
    def delete_all(cls):
        db.session.query(cls).delete()
        db.session.commit()

    @classmethod
    def search_by_username(cls, username, excluded_username):
        return cls.query \
            .filter(UserModel.username.like('%' + username + '%')) \
            .filter(UserModel.username != excluded_username) \
            .order_by(UserModel.username) \
            .limit(10) \
            .all()
