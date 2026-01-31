"""
Service para gerenciamento de agendamentos
Contém toda a lógica de negócio relacionada aos agendamentos
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
from models.agendamento_model import AgendamentoModel
from models.servicos_model import ServicoModel
from models.profissional_model import ProfissionalModel
from models.usuario_model import UsuarioModel


class AgendamentoService:
    """
    Service responsável pela lógica de negócio dos agendamentos
    """
    
    # Configurações de horário de funcionamento
    HORA_ABERTURA = 9  # 9h
    HORA_FECHAMENTO = 20  # 20h
    HORA_ALMOCO_INICIO = 12  # 12h
    HORA_ALMOCO_FIM = 13  # 13h
    
    # Durações dos serviços em minutos
    DURACAO_SERVICOS = {
        'alisamento': 30,
        'corte tesoura': 60,
        'corte maquina': 60,
        'barba': 30,
        'sobrancelha': 10,
        'pintura': 120
    }
    
    @staticmethod
    def criar_agendamento(dt_atendimento: datetime, id_user: int, 
                         id_profissional: int, servicos_ids: List[int],
                         observacoes: str = None) -> Dict:

        try:
            # Validações básicas
            if not AgendamentoService._validar_dados_basicos(
                dt_atendimento, id_user, id_profissional, servicos_ids):
                return {"erro": "Dados inválidos fornecidos"}
            
            # Verificar se a data não é no passado
            if dt_atendimento <= datetime.utcnow():
                return {"erro": "Não é possível agendar para datas passadas"}
            
            # Verificar horário de funcionamento
            if not AgendamentoService._verificar_horario_funcionamento(dt_atendimento):
                return {"erro": "Horário fora do funcionamento do estabelecimento"}
            
            # Buscar serviços e calcular duração total
            servicos = []
            duracao_total = 0
            valor_total = 0
            
            for servico_id in servicos_ids:
                servico = ServicoModel.find_by_id(servico_id)
                if not servico:
                    return {"erro": f"Serviço com ID {servico_id} não encontrado"}
                
                servicos.append(servico)
                duracao_total += AgendamentoService.DURACAO_SERVICOS.get(
                    servico.nome.lower(), 60)  # Default 60min se não encontrar
                valor_total += float(servico.preco)
            
            # Verificar disponibilidade de horário
            dt_fim = dt_atendimento + timedelta(minutes=duracao_total)
            if not AgendamentoService._verificar_disponibilidade(
                id_profissional, dt_atendimento, dt_fim):
                return {"erro": "Horário não disponível para o profissional"}
            
            # Criar agendamentos (um para cada serviço)
            agendamentos_criados = []
            dt_atual = dt_atendimento
            
            for i, servico in enumerate(servicos):
                duracao_servico = AgendamentoService.DURACAO_SERVICOS.get(
                    servico.nome.lower(), 60)
                
                agendamento = AgendamentoModel(
                    dt_atendimento=dt_atual,
                    id_user=id_user,
                    id_profissional=id_profissional,
                    id_servico=servico.id,
                    observacoes=observacoes if i == 0 else None,  # Observação só no primeiro
                    valor_total=float(servico.preco)
                )
                
                agendamento.save()
                agendamentos_criados.append(agendamento)
                
                # Próximo serviço começa após o atual
                dt_atual += timedelta(minutes=duracao_servico)
            
            return {
                "sucesso": True,
                "agendamentos": [ag.to_dict() for ag in agendamentos_criados],
                "valor_total": valor_total,
                "duracao_total": duracao_total
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    @staticmethod
    def cancelar_agendamento(agendamento_id: int, user_id: int) -> Dict:

        try:
            agendamento = AgendamentoModel.find_by_id(agendamento_id)
            
            if not agendamento:
                return {"erro": "Agendamento não encontrado"}
            
            if agendamento.id_user != user_id:
                return {"erro": "Acesso negado: agendamento não pertence ao usuário"}
            
            if agendamento.status == 'cancelado':
                return {"erro": "Agendamento já foi cancelado"}
            
            if agendamento.status == 'finalizado':
                return {"erro": "Não é possível cancelar um agendamento finalizado"}
            
            # Calcular taxa de cancelamento
            servico = ServicoModel.find_by_id(agendamento.id_servico)
            taxa = 0.0
            
            if not agendamento.pode_cancelar_gratuito():
                taxa = agendamento.calcular_taxa_cancelamento(float(servico.preco))
            
            # Atualizar agendamento
            agendamento.update(
                status='cancelado',
                taxa_cancelamento=taxa
            )
            
            return {
                "sucesso": True,
                "agendamento": agendamento.to_dict(),
                "taxa_cancelamento": taxa,
                "cancelamento_gratuito": taxa == 0
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    @staticmethod
    def listar_horarios_disponiveis(profissional_id: int, data: datetime.date) -> Dict:

        try:
            # Verificar se profissional existe
            if not ProfissionalModel.find_by_id(profissional_id):
                return {"erro": "Profissional não encontrado"}
            
            # Buscar agendamentos do dia
            agendamentos = AgendamentoModel.find_by_profissional_data(profissional_id, data)
            
            # Gerar slots de horário (intervalos de 30 min)
            horarios_disponiveis = []
            horarios_ocupados = set()
            
            # Marcar horários ocupados
            for agendamento in agendamentos:
                servico = ServicoModel.find_by_id(agendamento.id_servico)
                duracao = AgendamentoService.DURACAO_SERVICOS.get(
                    servico.nome.lower(), 60)
                
                inicio = agendamento.dt_atendimento
                fim = inicio + timedelta(minutes=duracao)
                
                # Marcar todos os slots ocupados
                slot_atual = inicio
                while slot_atual < fim:
                    horarios_ocupados.add(slot_atual.strftime("%H:%M"))
                    slot_atual += timedelta(minutes=30)
            
            # Gerar horários disponíveis
            data_completa = datetime.combine(data, time(AgendamentoService.HORA_ABERTURA))
            
            while data_completa.hour < AgendamentoService.HORA_FECHAMENTO:
                # Pular horário de almoço
                if (data_completa.hour >= AgendamentoService.HORA_ALMOCO_INICIO and 
                    data_completa.hour < AgendamentoService.HORA_ALMOCO_FIM):
                    data_completa += timedelta(minutes=30)
                    continue
                
                horario_str = data_completa.strftime("%H:%M")
                
                if horario_str not in horarios_ocupados:
                    horarios_disponiveis.append({
                        "horario": horario_str,
                        "timestamp": data_completa.isoformat()
                    })
                
                data_completa += timedelta(minutes=30)
            
            return {
                "sucesso": True,
                "data": data.isoformat(),
                "horarios_disponiveis": horarios_disponiveis
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    @staticmethod
    def listar_agendamentos_usuario(user_id: int, 
                                   status: str = None,
                                   data_inicio: datetime = None,
                                   data_fim: datetime = None) -> Dict:

        try:
            agendamentos = AgendamentoModel.find_by_user(user_id)
            
            # Aplicar filtros
            if status:
                agendamentos = [ag for ag in agendamentos if ag.status == status]
            
            if data_inicio:
                agendamentos = [ag for ag in agendamentos 
                               if ag.dt_atendimento >= data_inicio]
            
            if data_fim:
                agendamentos = [ag for ag in agendamentos 
                               if ag.dt_atendimento <= data_fim]
            
            # Enriquecer dados
            agendamentos_detalhados = []
            for agendamento in agendamentos:
                ag_dict = agendamento.to_dict()
                
                # Adicionar dados do serviço
                servico = ServicoModel.find_by_id(agendamento.id_servico)
                ag_dict['servico'] = {
                    'nome': servico.nome,
                    'preco': float(servico.preco),
                    'duracao': AgendamentoService.DURACAO_SERVICOS.get(
                        servico.nome.lower(), 60)
                }
                
                # Adicionar dados do profissional
                profissional = ProfissionalModel.find_by_id(agendamento.id_profissional)
                ag_dict['profissional'] = {
                    'nome': profissional.nome,
                    'especialidade': profissional.especialidade
                }
                
                agendamentos_detalhados.append(ag_dict)
            
            return {
                "sucesso": True,
                "agendamentos": agendamentos_detalhados
            }
            
        except Exception as e:
            return {"erro": f"Erro interno: {str(e)}"}
    
    @staticmethod
    def _validar_dados_basicos(dt_atendimento: datetime, id_user: int,
                              id_profissional: int, servicos_ids: List[int]) -> bool:

        if not isinstance(dt_atendimento, datetime):
            return False
        
        if not isinstance(id_user, int) or id_user <= 0:
            return False
        
        if not isinstance(id_profissional, int) or id_profissional <= 0:
            return False
        
        if not servicos_ids or not isinstance(servicos_ids, list):
            return False
        
        return True
    
    @staticmethod
    def _verificar_horario_funcionamento(dt_atendimento: datetime) -> bool:

        hora = dt_atendimento.hour
        
        # Verificar se está no horário de funcionamento
        if hora < AgendamentoService.HORA_ABERTURA or hora >= AgendamentoService.HORA_FECHAMENTO:
            return False
        
        # Verificar se não é horário de almoço
        if (hora >= AgendamentoService.HORA_ALMOCO_INICIO and 
            hora < AgendamentoService.HORA_ALMOCO_FIM):
            return False
        
        return True
    
    @staticmethod
    def _verificar_disponibilidade(profissional_id: int, dt_inicio: datetime,
                                  dt_fim: datetime) -> bool:

        agendamentos_conflito = AgendamentoModel.query.filter(
            AgendamentoModel.id_profissional == profissional_id,
            AgendamentoModel.status != 'cancelado',
            AgendamentoModel.dt_atendimento < dt_fim
        ).all()
        
        for agendamento in agendamentos_conflito:
            # Calcular fim do agendamento existente
            servico = ServicoModel.find_by_id(agendamento.id_servico)
            duracao = AgendamentoService.DURACAO_SERVICOS.get(
                servico.nome.lower(), 60)
            ag_fim = agendamento.dt_atendimento + timedelta(minutes=duracao)
            
            # Verificar sobreposição
            if not (dt_fim <= agendamento.dt_atendimento or dt_inicio >= ag_fim):
                return False
        
        return True
