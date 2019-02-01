import datetime

from src.app import db


class TourPassengerLinkModel(db.Model):
    __tablename__ = 'tour_passenger_link'

    tour_id = db.Column(db.Integer, db.ForeignKey('tours.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    tour = db.relationship('TourModel')
    user = db.relationship('UserModel')
    time_created = db.Column(db.DateTime(), default=datetime.datetime.utcnow)
    time_updated = db.Column(db.DateTime(), onupdate=datetime.datetime.utcnow)

    def persist(self):
        db.session.add(self)
        db.session.commit()
