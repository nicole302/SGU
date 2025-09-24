from flask import (  # app Flask e objeto request para inspecionar endpoint atual
    Flask,
    request,
)
from flask_cors import CORS  # habilita CORS (cross-origin requests)
from flask_marshmallow import Marshmallow  # serialização/validação de schemas
from flask_migrate import Migrate  # migrações do banco (Alembic)
from flask_restful import Api  # estrutura para criar APIs REST
from flask_sqlalchemy import SQLAlchemy  # ORM para modelagem do banco

app = Flask(__name__)  # instância da aplicação Flask
app.config.from_object('connection')

# configuração das extensões vinculadas à app
db = SQLAlchemy(app)  # objeto do SQLAlchemy para manipular o banco
migrate = Migrate(app, db)  # gerenciador de migrações (alinha o ORM com o banco)
ma = Marshmallow(app)  # Marshmallow para (de)serialização e validação
api = Api(app)  # wrapper para rotas RESTful
CORS(app)  # aplica CORS com configuração padrão


@app.before_request
def create_tables():
    # cria todas as tabelas definidas pelos modelos apenas quando o endpoint for "index"
    # OBS: chamar db.create_all() em requisições pode ser útil em desenvolvimento,
    # mas não é recomendado em produção — prefira migrações.
    if request.endpoint == "index":
        db.create_all()


# importa os módulos de modelos
from .models import agendamento_model, profissional_model, servicos_model, usuario_model

# TODO - Importar as views para a API para as rotas
from .views import usuario_view
