from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from jinja2 import Environment, PackageLoader, select_autoescape

app = Flask(__name__)
cors = CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:4300",
            "https://carbulator.net"
        ]
    }
})
api = Api(app, prefix='/api')

app.config.from_object('src.config.default.DefaultConfig')
app.config.from_envvar('CARBULATOR_CONFIG')

jwt = JWTManager(app)

db = SQLAlchemy(app)

env = Environment(
    loader=PackageLoader('src', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)

from src.models.revoked_token import RevokedTokenModel


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    return RevokedTokenModel.is_jti_blacklisted(jti)


from src.api import configure_api

configure_api(api)

migrate = Migrate(app, db, compare_type=False)
