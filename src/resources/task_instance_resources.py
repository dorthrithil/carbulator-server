from datetime import datetime
from typing import List

import pytz
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, abort

from src.messages.messages import UNAUTHORIZED
from src.models.community import CommunityModel
from src.models.task import TaskModel
from src.models.task_instance import TaskInstanceModel
from src.models.user import UserModel


def create_km_triggered_task_instances(community_id, km):
    """
    Checks if there are new task instances that have to be created and creates them.
    :param community_id: Community to check the task instance creation for.
    :param km: Current km clock.
    """
    tasks = TaskModel.find_by_community(community_id)

    # Iterate over all km triggered tasks
    for task in [t for t in tasks if t.km_interval]:

        try:
            # If current km are higher then trigger, add a new task instance
            if km >= task.km_next_instance:
                # Create and persist task instance
                new_task_instance = TaskInstanceModel()
                new_task_instance.task = task
                new_task_instance.km_created_at = km
                new_task_instance.is_open = True
                new_task_instance.community = task.community
                new_task_instance.persist()

                # Update km trigger and persist task
                task.km_next_instance += task.km_interval
                if task.km_next_instance <= km:
                    task.km_next_instance = km + 1
                task.persist()
        except:
            # Don't fail on all just because one instance is bad
            pass


def create_time_triggered_task_instances():
    """
    Checks if there are new task instances that have to be created and creates them.
    """
    tasks = TaskModel.return_all()

    # Iterate over all time triggered tasks
    for task in [t for t in tasks if t.time_interval]:

        try:
            # If current time is higher then trigger, add a new task instance
            now = datetime.now(pytz.utc)
            then = task.time_next_instance.replace(tzinfo=pytz.utc)

            if now >= then:
                # Create and persist task instance
                new_task_instance = TaskInstanceModel()
                new_task_instance.task = task
                new_task_instance.is_open = True
                new_task_instance.community = task.community
                new_task_instance.persist()

                # Update time trigger and persist task
                task.time_next_instance = now + task.time_interval
                task.persist()
        except:
            # Don't fail on all just because one instance is bad
            pass


class GetOpenCommunityTaskInstances(Resource):

    @jwt_required
    @marshal_with(TaskInstanceModel.get_marshaller())
    def get(self, community_id):
        community: CommunityModel = CommunityModel.find_by_id(community_id)
        community_member_ids = [m.id for m in community.users]
        user = UserModel.find_by_username(get_jwt_identity())

        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        task_instances: List[TaskInstanceModel] = TaskInstanceModel.find_by_community(community_id)
        open_task_instances = [i for i in task_instances if i.is_open]

        return open_task_instances, 200


class GetOpenAccountTaskInstances(Resource):

    @jwt_required
    @marshal_with(TaskInstanceModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())
        all_communities = CommunityModel.return_all()
        user_communities = [c for c in all_communities if user.id in [u.id for u in c.users]]

        task_instances = []
        for c in user_communities:
            task_instances += TaskInstanceModel.find_by_community(c.id)
        open_task_instances = [i for i in task_instances if i.is_open]

        return open_task_instances, 200


class FinishTaskInstances(Resource):

    @jwt_required
    @marshal_with(TaskInstanceModel.get_marshaller())
    def put(self, task_instance_id):
        user = UserModel.find_by_username(get_jwt_identity())
        task_instance: TaskInstanceModel = TaskInstanceModel.find_by_id(task_instance_id)

        community_member_ids = [m.id for m in task_instance.community.users]
        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        task_instance.is_open = False
        task_instance.time_finished = datetime.now()
        task_instance.finished_by = user
        task_instance.persist()

        return task_instance, 200
