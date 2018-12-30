from flask_restful import fields

from src.app import db
from src.exceptions.no_data import NoData
from src.models.task import TaskModel
from src.models.user import UserModel


class TaskInstanceModel(db.Model):
    __tablename__ = 'task_instances'

    id = db.Column(db.Integer, primary_key=True)
    time_created = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    time_updated = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    task = db.relationship('TaskModel', foreign_keys=[task_id])
    km_created_at = db.Column(db.DECIMAL(precision=10, scale=1), nullable=True)
    is_open = db.Column(db.Boolean)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False)
    community = db.relationship('CommunityModel')
    time_finished = db.Column(db.DateTime(timezone=True), nullable=True)
    finished_by = db.relationship('UserModel')
    finished_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


    def persist(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_marshaller():
        return {
            'id': fields.Integer,
            'time_created': fields.DateTime,
            'time_updated': fields.DateTime,
            'time_finished': fields.DateTime,
            'task': fields.Nested(TaskModel.get_marshaller()),
            'is_open': fields.Boolean,
            'km_created_at': fields.Float,
            'finished_by': fields.Nested(UserModel.get_marshaller())
        }

    @classmethod
    def delete_by_id(cls, task_instance_id):
        task = db.session.query(cls).filter(cls.id == task_instance_id).first()
        if task:
            db.session.delete(task)
            db.session.commit()
        else:
            raise NoData

    @classmethod
    def find_by_id(cls, task_instance_id):
        return cls.query.filter_by(id=task_instance_id).first()

    @classmethod
    def find_by_task(cls, task_id):
        return cls.query \
            .filter_by(task_id=task_id) \
            .all()

    @classmethod
    def find_by_community(cls, community_id):
        return cls.query \
            .filter_by(community_id=community_id) \
            .all()
