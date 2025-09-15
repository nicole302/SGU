from src import db


class Login(db.Model):
    __tablename__= 'tb_login'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), nullable=False)
    senha = db.Column(db.String(120), nullable=False)
