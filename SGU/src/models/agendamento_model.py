# importação das bibliotecas necessárias
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from src import db

# criação da tabela de agendamentos
class AgendamentoModel(db.Model):

    __tablename__ = 'tb_agendamentos'
    
    # Campos principais
    id = Column(Integer, primary_key=True, autoincrement=True)
    dt_agendamento = Column(DateTime, nullable=False, default=datetime.utcnow)
    dt_atendimento = Column(DateTime, nullable=False)
    
    # Chaves estrangeiras
    id_user = Column(Integer, ForeignKey('tb_usuario.id'), nullable=False)
    id_profissional = Column(Integer, ForeignKey('tb_profissional.id'), nullable=False)
    id_servico = Column(Integer, ForeignKey('tb_servico.id'), nullable=False)
    
    # Campos adicionais
    status = Column(String(20), nullable=False, default='agendado')
    valor_total = Column(Float, nullable=False, default=0.00)
    taxa_cancelamento = Column(Float, nullable=True, default=0.00)
    
    # Relacionamentos
    usuario = relationship("UsuarioModel", backref="agendamentos")
    profissional = relationship("ProfissionalModel", backref="agendamentos")
    servico = relationship("ServicoModel", backref="agendamentos")
    
    #construtor
    def __init__(self, dt_atendimento, id_user, id_profissional, id_servico, valor_total=0.00):

        self.dt_atendimento = dt_atendimento
        self.id_user = id_user
        self.id_profissional = id_profissional
        self.id_servico = id_servico
        self.valor_total = valor_total
        self.dt_agendamento = datetime.utcnow()
        self.status = 'agendado'
 