from ..models.usuario_model import UsuarioModel
from ..entities.usuario import Usuario
from src import db


def cadastrar_usuario(usuario_entity):
    usuario_db = UsuarioModel(
        nome=usuario_entity.nome,
        email=usuario_entity.email,
        telefone=usuario_entity.telefone,
        senha=usuario_entity.senha)
    
    # criptografa a senha
    usuario_db.gen_senha(usuario_entity.senha)
    db.session.add(usuario_db)
    db.session.commit()
    return usuario_db


def listar_usuario():
    usuario_db = UsuarioModel.query.all()
    usuario_enti = [
        Usuario(u.nome, u.email, u.telefone, u.senha) for u in usuario_db
    ]
    return usuario_enti


def listar_usuario_email(email):
    usuario_db = UsuarioModel.query.filter_by(email=email).first()
    
    if usuario_db:
        return Usuario(usuario_db.nome,
                       usuario_db.email,
                       usuario_db.telefone,
                       usuario_db.senha)
        
    return None

   
def listar_usuario_id(id): 
    try:
        # buscar usuario
        usuario_encontrado = UsuarioModel.query.get(id)
        if usuario_encontrado:
            return Usuario(usuario_encontrado.nome,
                           usuario_encontrado.email,
                           usuario_encontrado.telefone,
                           usuario_encontrado.senha)
    except Exception as e:
        print(f'Erro ao listar usuario por id {e}')
        return None

def editar_usuario(id, usuario_entity):
    usuario_db = UsuarioModel.query.get(id)
    
    if not usuario_db:
       return None
        
    usuario_db.nome = usuario_entity.nome
    usuario_db.telefone = usuario_entity.telefone
    
    if usuario_entity.senha:
        usuario_db.gen_senha(usuario_entity.senha)
        
    db.session.commit()    
    
    return Usuario(
        nome=usuario_db.nome,
        email=usuario_db.email,
        telefone=usuario_db.telefone,
        senha=usuario_db.senha
    )
    
    
def excluir_usuario(id):
    usuario_db = UsuarioModel.query.get(id)
    if not usuario_db:
        return False 
    db.session.delete(usuario_db)
    db.session.commit()
    return True 
    
def editar_usuario(id, usuario_entity):
    usuario_db = UsuarioModel.query.get(id)
    
    if not usuario_db:
        return None

    usuario_db.nome = usuario_entity.nome
    usuario_db.telefone = usuario_entity.telefone

    if usuario_entity.senha:
        usuario_db.gen_senha(usuario_entity.senha)

    db.session.commit()

    return Usuario(
        nome = usuario_db.nome,
        email= usuario_db.email,
        telefone=usuario_db.telefone,
        senha=usuario_db.senha
    )      

def listar_usuario_email(email):
    usuario_db = UsuarioModel.query.filter_by(email = email).first()

    if usuario_db:
        return Usuario(
            usuario_db.nome,
            usuario_db.email,
            usuario_db.telefone,
            usuario_db.senha
        )
    
    return None

