from flask_restful import Resource
from marshmallow import ValidationError
from src.schemas import usuario_schema
from src.entities import usuario
from flask import request, jsonify, make_response
from src.services import usuario_services
from src import api


# POST-GET-PUT-DELETE
# Lidar com todos os usuarios
class UsuarioList(Resource):
    def get(self):
        usuarios = usuario_services.listar_usuario()

        if not usuarios:
            return make_response(jsonify({'message':'Não existe usuarios!'}))

        schema = usuario_schema.UsuarioSchema(many=True)
        return make_response(jsonify(schema.dump(usuarios)), 200)

    def post(self):
        schema = usuario_schema.UsuarioSchema()

        try:
            dados = schema.load(request.json)
        except ValidationError as err:
            return make_response(jsonify(err.messages), 400)    
        
        if usuario_services.listar_usuario_email(dados['email']):
            return make_response(jsonify({'message': 'Email já cadastrado'}), 400)
        
        try:
            # criação do novo usuario no banco
            novo_usurio = usuario.Usuario(
                nome=dados['nome'],
                email=dados['email'],
                telefone=dados['telefone'],
                senha=dados['senha']
                    
            )
            resultado = usuario_services.cadastrar_usuario(novo_usurio)
            return make_response(jsonify(schema.dump(resultado)), 201)
        
        except Exception as e:
            return make_response(jsonify({'message':str(e)}), 400)


api.add_resource(UsuarioList, '/usuario')            

class UsuarioResource(Resource):
    def get(self, id_usuario):
        usuario_encontrado = usuario_services.listar_usuario_id(id_usuario)
        if not usuario_encontrado:
            return make_response(jsonify({'message': 'Usuário não encontrado'}))
        
        schema = usuario_schema.UsuarioSchema()
        return make_response(jsonify(schema.dump(usuario_encontrado)), 200)
    
    def put(self, id_usuario):
        ...
    def delete(self, id_usuario):
        usuario_encontrado = usuario_services.listar_usuario_id(id_usuario)
        if not usuario_encontrado:
            return make_response(jsonify({'message': 'Usuário não encontrado'}), 404)
        try:
            usuario_services.excluir_usuario(id_usuario)
            return make_response(jsonify({'message': 'Usuário excluído com sucesso!'}), 200)
        except Exception as e:
            return make_response(jsonify({'message':str(e)}),400)

api.add_resource(UsuarioResource, '/usuario/<int:id_usuario>') # /usuario/1                    
