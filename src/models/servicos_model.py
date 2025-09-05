from src import db

class Servico(db.Model):
    __tablename__ = 'tb_servico'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    descricao = db.Column(db.String(120), nullavle=False)
    valor = db.Column(db.Float, nullabe=False)

    def __init__(self, descricao, valogir):
        self.descricao = descricao
        self.valor 
