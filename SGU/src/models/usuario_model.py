from src import db
from passlib.hash import pbkdf2_sha256 as sha256

class UsuarioModel(db.Model):
    __tablename__ = 'tb_usuario'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    telefone = db.Column(db.String(50), nullable=False)
    senha = db.Column(db.String(120), nullable=False)


    def gen_senha(self, senha):
        self.senha = sha256.hash(senha)

    def verficar_senha(self, senha):
        return sha256.verify(senha, self.senha)    
