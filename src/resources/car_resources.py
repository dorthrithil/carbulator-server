from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, marshal_with, reqparse, abort

from src.exceptions.no_data import NoData
from src.messages.marshalling_objects import SimpleMessage
from src.messages.messages import CAR_DELETED, INTERNAL_SERVER_ERROR, CAR_DOESNT_EXIST
from src.models.car import CarModel
from src.models.user import UserModel

parser = reqparse.RequestParser()
parser.add_argument('name', help='This field cannot be blank', required=True, type=str)
parser.add_argument('make', help='This field cannot be blank', required=True, type=str)
parser.add_argument('model', help='This field cannot be blank', required=True, type=str)


class SingleCar(Resource):

    @jwt_required
    @marshal_with(CarModel.get_marshaller())
    def get(self, id):
        car = CarModel.find_by_id(id)
        if not car:
            abort(404, message=CAR_DOESNT_EXIST)
        return car, 200

    @jwt_required
    @marshal_with(CarModel.get_marshaller())
    def put(self, id):
        data = parser.parse_args()

        car = CarModel.find_by_id(id)

        if not car:
            abort(404, message=CAR_DOESNT_EXIST)

        car.name = data['name']
        car.make = data['make']
        car.model = data['model']
        car.persist()

        return car, 200

    @jwt_required
    @marshal_with(SimpleMessage.get_marshaller())
    def delete(self, id):
        try:
            CarModel.delete_by_id(id)
        except NoData:
            abort(404, message=CAR_DOESNT_EXIST)
        return SimpleMessage(CAR_DELETED), 200


class AllCars(Resource):

    @jwt_required
    @marshal_with(CarModel.get_marshaller())
    def post(self):
        data = parser.parse_args()

        owner = UserModel.find_by_username(get_jwt_identity())

        new_car = CarModel(
            owner=owner,
            name=data['name'],
            make=data['make'],
            model=data['model'],
        )

        try:
            new_car.persist()
            return new_car, 201
        except:
            abort(500, message=INTERNAL_SERVER_ERROR)


class UserCars(Resource):

    @jwt_required
    @marshal_with(CarModel.get_marshaller())
    def get(self):
        user = UserModel.find_by_username(get_jwt_identity())
        return CarModel.return_all_for_user(user.id), 200
