from datetime import timedelta, datetime
from typing import List

import pytz
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, reqparse, abort

from src.messages.marshalling_objects import SimpleMessage
from src.messages.messages import COMMUNIY_DOESNT_EXIST, UNAUTHORIZED, TASK_MUST_BE_EITHER_TIME_OR_KM_TRIGGERED, \
    INTERNAL_SERVER_ERROR, TASK_DOESNT_EXIST, TASK_DELETED, TASK_KM_NEXT_INSTANCE_MUST_BE_HIGHER_THEN_CURRENT_KM, \
    TASK_TIME_NEXT_INSTANCE_MUST_BE_HIGHER_THEN_CURRENT_TIME, NON_REOCURRENT_TASKS_CANNOT_BE_UPDATED
from src.models.community import CommunityModel
from src.models.task import TaskModel
from src.models.task_instance import TaskInstanceModel
from src.models.tour import TourModel
from src.models.user import UserModel
from src.util.parser_types import moment


def set_km_to_next_instance(tasks):
    """
    Sets the `km_to_next_instance` property on the given task or list of tasks.
    :param tasks: Task or list of tasks.
    """
    is_list = isinstance(tasks, (list,))
    if not is_list:
        tasks = [tasks]
    if len(tasks) > 0:
        latest_tour = TourModel.find_newest_tour_for_community(tasks[0].community.id)
        for task in tasks:
            if task.km_next_instance:
                task.km_to_next_instance = task.km_next_instance - latest_tour.end_km


class CreateTask(Resource):

    @jwt_required
    @marshal_with(TaskModel.get_marshaller())
    def post(self, community_id):
        parser = reqparse.RequestParser()
        parser.add_argument('time_next_instance', type=moment, required=False)
        parser.add_argument('time_interval', type=int, required=False)
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('km_interval', type=int, required=False)
        parser.add_argument('km_next_instance', type=float, required=False)
        parser.add_argument('is_reocurrent', type=bool, required=True)
        data = parser.parse_args()

        owner = UserModel.find_by_username(get_jwt_identity())
        community: CommunityModel = CommunityModel.find_by_id(community_id)
        community_member_ids = [m.id for m in community.users]

        if not community:
            abort(400, message=COMMUNIY_DOESNT_EXIST)

        if owner.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        if data['is_reocurrent'] and (
                not (data['time_next_instance'] and data['time_interval'] or data['km_interval'] and data[
            'km_next_instance']) or data['km_interval'] and (data['time_interval'] or data['time_next_instance']) or \
                data['time_interval'] and (data['km_interval'] or data['km_next_instance'])):
            abort(400, message=TASK_MUST_BE_EITHER_TIME_OR_KM_TRIGGERED)

        newest_tour: TourModel = TourModel.find_newest_tour_for_community(community_id)
        if data['km_next_instance'] and data['km_next_instance'] < newest_tour.end_km:
            abort(400, message=TASK_KM_NEXT_INSTANCE_MUST_BE_HIGHER_THEN_CURRENT_KM)

        if data['time_next_instance'] and data['time_next_instance'] < datetime.now(pytz.timezone('Europe/Berlin')):
            abort(400, message=TASK_TIME_NEXT_INSTANCE_MUST_BE_HIGHER_THEN_CURRENT_TIME)

        time_interval = None
        if data['time_interval']:
            time_interval = timedelta(days=data['time_interval'])

        new_task = TaskModel(
            owner=owner,
            community=community,
            time_interval=time_interval,
            time_next_instance=data['time_next_instance'],
            km_interval=data['km_interval'],
            km_next_instance=data['km_next_instance'],
            name=data['name'],
            description=data['description'],
            is_reocurrent=data['is_reocurrent']
        )

        try:
            new_task.persist()
            set_km_to_next_instance(new_task)

            if not data['is_reocurrent']:
                new_task_instance = TaskInstanceModel(
                    task=new_task,
                    is_open=True,
                    community=new_task.community
                )
                new_task_instance.persist()

            return new_task, 201
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class UpdateTask(Resource):

    @jwt_required
    @marshal_with(TaskModel.get_marshaller())
    def put(self, task_id):
        parser = reqparse.RequestParser()
        parser.add_argument('time_next_instance', type=moment, required=False)
        parser.add_argument('time_interval', type=int, required=False)
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        parser.add_argument('km_interval', type=int, required=False)
        parser.add_argument('km_next_instance', type=float, required=False)
        data = parser.parse_args()

        task: TaskModel = TaskModel.find_by_id(task_id)

        if not task:
            abort(404, message=TASK_DOESNT_EXIST)

        if not task.is_reocurrent:
            abort(401, message=NON_REOCURRENT_TASKS_CANNOT_BE_UPDATED)

        community_member_ids = [m.id for m in task.community.users]
        user = UserModel.find_by_username(get_jwt_identity())

        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        if not (data['time_next_instance'] and data['time_interval'] or data['km_interval'] and data[
            'km_next_instance']) or data['km_interval'] and (data['time_interval'] or data['time_next_instance']) or \
                data['time_interval'] and (data['km_interval'] or data['km_next_instance']):
            abort(400, message=TASK_MUST_BE_EITHER_TIME_OR_KM_TRIGGERED)

        time_interval = None
        if data['time_interval']:
            time_interval = timedelta(days=data['time_interval'])

        task.time_interval = time_interval
        task.time_next_instance = data['time_next_instance']
        task.km_interval = data['km_interval']
        task.km_next_instance = data['km_next_instance']
        task.name = data['name']
        task.description = data['description']

        try:
            task.persist()
            set_km_to_next_instance(task)
            return task, 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class GetTask(Resource):

    @jwt_required
    @marshal_with(TaskModel.get_marshaller())
    def get(self, task_id):

        task: TaskModel = TaskModel.find_by_id(task_id)

        if not task:
            abort(404, message=TASK_DOESNT_EXIST)

        community_member_ids = [m.id for m in task.community.users]
        user = UserModel.find_by_username(get_jwt_identity())

        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        set_km_to_next_instance(task)

        return task, 200


class GetCommunityTasks(Resource):

    @jwt_required
    @marshal_with(TaskModel.get_marshaller())
    def get(self, community_id):
        tasks: List[TaskModel] = TaskModel.find_by_community(community_id)
        community: CommunityModel = CommunityModel.find_by_id(community_id)
        community_member_ids = [m.id for m in community.users]
        user = UserModel.find_by_username(get_jwt_identity())

        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        set_km_to_next_instance(tasks)

        return tasks, 200


class DeleteTask(Resource):

    @jwt_required
    @marshal_with(SimpleMessage.get_marshaller())
    def delete(self, task_id):

        task: TaskModel = TaskModel.find_by_id(task_id)

        if not task:
            abort(400, message=TASK_DOESNT_EXIST)

        community_member_ids = [m.id for m in task.community.users]
        user = UserModel.find_by_username(get_jwt_identity())

        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        try:
            task.delete_by_id(task_id)
            return SimpleMessage(TASK_DELETED), 200
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)
