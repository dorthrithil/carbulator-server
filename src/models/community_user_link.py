from flask_restful import fields

from src.app import db
from src.models.community import CommunityModel


class CommunityUserLinkModel(db.Model):
    __tablename__ = 'community_user_link'

    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    is_owner = db.Column(db.Boolean, default=True)
    invitation_accepted = db.Column(db.Boolean, default=True)
    community = db.relationship('CommunityModel')
    user = db.relationship('UserModel')
    time_created = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'community': fields.Nested(CommunityModel.get_marshaller()),
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime,
        }

    @classmethod
    def find_by_user_and_community(cls, user_id, community_id):
        return cls.query.filter_by(user_id=user_id, community_id=community_id).first()

    @classmethod
    def find_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id).all()

    @classmethod
    def find_open_invitations_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id, invitation_accepted=False).all()

    @classmethod
    def find_open_invitations_by_community(cls, community_id):
        return cls.query.filter_by(community_id=community_id, invitation_accepted=False).all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
