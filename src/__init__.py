from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_restful import Api

app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)
api = Api(app)
CORS(app)

@app.before_request
def create_tables():
    if request.endpoint == 'index':
        db.create_all()

from .models import agendamento, logjn, profissional_model, servicos_model, usuario_model        
# TODO: Importar as views para a API encontrar as rotas
