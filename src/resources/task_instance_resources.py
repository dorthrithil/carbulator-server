from typing import List

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
            task.km_next_instance = task.km_interval
            task.persist()


class GetOpenCommunityTaskInstances(Resource):

    @jwt_required
    @marshal_with(TaskInstanceModel.get_marshaller())
    def get(self, community_id):
        community: CommunityModel = CommunityModel.find_by_id(community_id)
        community_member_ids = [m.id for m in community.users]
        user = UserModel.find_by_username(get_jwt_identity())

        task_instances: List[TaskModel] = TaskInstanceModel.find_by_community(community_id)

        if user.id not in community_member_ids:
            abort(401, message=UNAUTHORIZED)

        return task_instances, 200
