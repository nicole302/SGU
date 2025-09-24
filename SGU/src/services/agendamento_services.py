"""
Service para gerenciamento de agendamentos
Adaptado para funcionar com SQLAlchemy Models e Marshmallow Schemas
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
from src.models.agendamento_model import AgendamentoModel
from src.models.servicos_model import ServicoModel
from src.models.profissional_model import ProfissionalModel
from src.models.usuario_model import UsuarioModel
from src import db


class AgendamentoService:
    """
    Service responsável pela lógica de negócio dos agendamentos
    """
    
    # Configurações de horário de funcionamento
    HORA_ABERTURA = 9  # 9h
    HORA_FECHAMENTO = 20  # 20h
    HORA_ALMOCO_INICIO = 12  # 12h
    HORA_ALMOCO_FIM = 13  # 13h
    
    # Duração padrão em minutos (fallback caso não esteja no banco)
    DURACAO_PADRAO = 60


def _obter_duracao_servico(servico):
    """Obtém duração do serviço do banco ou usa fallback"""
    # Primeiro tenta pegar do campo duracao
    if hasattr(servico, 'duracao') and servico.duracao:
        return servico.duracao
    
    # Se não existir, usa duração padrão
    return AgendamentoService.DURACAO_PADRAO


def listar_agendamentos():
    """Lista todos os agendamentos"""
    try:
        return AgendamentoModel.query.all()
    except Exception as e:
        raise Exception(f"Erro ao listar agendamentos: {str(e)}")


def listar_agendamento_id(agendamento_id: int):
    """Lista um agendamento específico por ID"""
    try:
        return AgendamentoModel.query.get(agendamento_id)
    except Exception as e:
        raise Exception(f"Erro ao buscar agendamento: {str(e)}")


def cadastrar_agendamento(novo_agendamento):
    """
    Cadastra um novo agendamento com todas as validações de negócio
    """
    try:
        # Validações básicas
        if not _validar_dados_basicos(
            novo_agendamento.dt_atendimento, 
            novo_agendamento.id_user,
            novo_agendamento.id_profissional, 
            novo_agendamento.id_servico
        ):
            raise Exception("Dados inválidos fornecidos")
        
        # Verificar se a data não é no passado
        if novo_agendamento.dt_atendimento <= datetime.now():
            raise Exception("Não é possível agendar para datas passadas")
        
        # Verificar horário de funcionamento
        if not _verificar_horario_funcionamento(novo_agendamento.dt_atendimento):
            raise Exception("Horário fora do funcionamento do estabelecimento")
        
        # Verificar se o usuário existe
        usuario = UsuarioModel.query.get(novo_agendamento.id_user)
        if not usuario:
            raise Exception("Usuário não encontrado")
        
        # Verificar se o profissional existe
        profissional = ProfissionalModel.query.get(novo_agendamento.id_profissional)
        if not profissional:
            raise Exception("Profissional não encontrado")
        
        # Verificar se o serviço existe e calcular duração
        servico = ServicoModel.query.get(novo_agendamento.id_servico)
        if not servico:
            raise Exception("Serviço não encontrado")
        
        # Calcular duração e horário de fim usando o banco de dados
        duracao_servico = _obter_duracao_servico(servico)
        dt_fim = novo_agendamento.dt_atendimento + timedelta(minutes=duracao_servico)
        
        # Verificar disponibilidade de horário
        if not _verificar_disponibilidade(
            novo_agendamento.id_profissional, 
            novo_agendamento.dt_atendimento, 
            dt_fim
        ):
            raise Exception("Horário não disponível para o profissional")
        
        # Se valor_total não foi fornecido, usar o preço do serviço
        if novo_agendamento.valor_total == 0.00:
            novo_agendamento.valor_total = float(servico.preco)
        
        # Salvar no banco
        db.session.add(novo_agendamento)
        db.session.commit()
        
        return novo_agendamento
        
    except Exception as e:
        db.session.rollback()
        raise Exception(str(e))


def editar_agendamento(agendamento_id: int, dados_atualizados):
    """
    Edita um agendamento existente
    """
    try:
        agendamento_existente = AgendamentoModel.query.get(agendamento_id)
        if not agendamento_existente:
            raise Exception("Agendamento não encontrado")
        
        # Verificar se pode ser editado (não cancelado/concluído)
        if agendamento_existente.status in ['cancelado', 'concluido']:
            raise Exception("Não é possível editar agendamento cancelado ou concluído")
        
        # Validações se estiver alterando data/hora
        if dados_atualizados.dt_atendimento != agendamento_existente.dt_atendimento:
            # Verificar se a nova data não é no passado
            if dados_atualizados.dt_atendimento <= datetime.utcnow():
                raise Exception("Não é possível agendar para datas passadas")
            
            # Verificar horário de funcionamento
            if not _verificar_horario_funcionamento(dados_atualizados.dt_atendimento):
                raise Exception("Horário fora do funcionamento do estabelecimento")
        
        # Validações se estiver alterando profissional ou serviço
        if (dados_atualizados.id_profissional != agendamento_existente.id_profissional or
            dados_atualizados.id_servico != agendamento_existente.id_servico or
            dados_atualizados.dt_atendimento != agendamento_existente.dt_atendimento):
            
            # Verificar se o profissional existe
            profissional = ProfissionalModel.query.get(dados_atualizados.id_profissional)
            if not profissional:
                raise Exception("Profissional não encontrado")
            
            # Verificar se o serviço existe
            servico = ServicoModel.query.get(dados_atualizados.id_servico)
            if not servico:
                raise Exception("Serviço não encontrado")
            
            # Calcular duração e verificar disponibilidade
            duracao_servico = _obter_duracao_servico(servico)
            dt_fim = dados_atualizados.dt_atendimento + timedelta(minutes=duracao_servico)
            
            if not _verificar_disponibilidade_edicao(
                dados_atualizados.id_profissional, 
                dados_atualizados.dt_atendimento, 
                dt_fim,
                agendamento_id
            ):
                raise Exception("Horário não disponível para o profissional")
        
        # Atualizar campos
        agendamento_existente.dt_atendimento = dados_atualizados.dt_atendimento
        agendamento_existente.id_user = dados_atualizados.id_user
        agendamento_existente.id_profissional = dados_atualizados.id_profissional
        agendamento_existente.id_servico = dados_atualizados.id_servico
        agendamento_existente.valor_total = dados_atualizados.valor_total
        
        db.session.commit()
        return agendamento_existente
        
    except Exception as e:
        db.session.rollback()
        raise Exception(str(e))


def excluir_agendamento(agendamento_id: int):
    """
    Exclui um agendamento (cancelamento)
    """
    try:
        agendamento = AgendamentoModel.query.get(agendamento_id)
        if not agendamento:
            raise Exception("Agendamento não encontrado")
        
        if agendamento.status == 'cancelado':
            raise Exception("Agendamento já foi cancelado")
        
        if agendamento.status == 'concluido':
            raise Exception("Não é possível cancelar um agendamento concluído")
        
        # Calcular taxa de cancelamento se necessário
        servico = ServicoModel.query.get(agendamento.id_servico)
        taxa = 0.0
        
        if not _pode_cancelar_gratuito(agendamento):
            taxa = _calcular_taxa_cancelamento(float(servico.preco))
        
        # Atualizar status para cancelado
        agendamento.status = 'cancelado'
        agendamento.taxa_cancelamento = taxa
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        raise Exception(str(e))


def listar_horarios_disponiveis(profissional_id: int, data_str: str) -> Dict:
    """
    Lista horários disponíveis para um profissional em uma data específica
    """
    try:
        # Converter string para date
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
        
        # Verificar se profissional existe
        profissional = ProfissionalModel.query.get(profissional_id)
        if not profissional:
            raise Exception("Profissional não encontrado")
        
        # Buscar agendamentos do dia
        data_inicio = datetime.combine(data, time.min)
        data_fim = datetime.combine(data, time.max)
        
        agendamentos = AgendamentoModel.query.filter(
            AgendamentoModel.id_profissional == profissional_id,
            AgendamentoModel.dt_atendimento >= data_inicio,
            AgendamentoModel.dt_atendimento <= data_fim,
            AgendamentoModel.status != 'cancelado'
        ).all()
        
        # Gerar slots de horário (intervalos de 30 min)
        horarios_disponiveis = []
        horarios_ocupados = set()
        
        # Marcar horários ocupados
        for agendamento in agendamentos:
            servico = ServicoModel.query.get(agendamento.id_servico)
            duracao = _obter_duracao_servico(servico)
            
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
            "data": data.isoformat(),
            "horarios_disponiveis": horarios_disponiveis
        }
        
    except Exception as e:
        raise Exception(f"Erro ao listar horários disponíveis: {str(e)}")


def listar_agendamentos_usuario(user_id: int, status: str = None) -> List:
    """
    Lista agendamentos de um usuário específico
    """
    try:
        query = AgendamentoModel.query.filter_by(id_user=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.all()
        
    except Exception as e:
        raise Exception(f"Erro ao listar agendamentos do usuário: {str(e)}")


# Funções auxiliares privadas
def _validar_dados_basicos(dt_atendimento: datetime, id_user: int,
                          id_profissional: int, id_servico: int) -> bool:
    """Valida dados básicos do agendamento"""
    if not isinstance(dt_atendimento, datetime):
        return False
    
    if not isinstance(id_user, int) or id_user <= 0:
        return False
    
    if not isinstance(id_profissional, int) or id_profissional <= 0:
        return False
    
    if not isinstance(id_servico, int) or id_servico <= 0:
        return False
    
    return True


def _verificar_horario_funcionamento(dt_atendimento: datetime) -> bool:
    """Verifica se o horário está dentro do funcionamento"""
    hora = dt_atendimento.hour
    
    # Verificar se está no horário de funcionamento
    if hora < AgendamentoService.HORA_ABERTURA or hora >= AgendamentoService.HORA_FECHAMENTO:
        return False
    
    # Verificar se não é horário de almoço
    if (hora >= AgendamentoService.HORA_ALMOCO_INICIO and 
        hora < AgendamentoService.HORA_ALMOCO_FIM):
        return False
    
    return True


def _verificar_disponibilidade(profissional_id: int, dt_inicio: datetime,
                              dt_fim: datetime) -> bool:
    """Verifica se o horário está disponível para o profissional"""
    agendamentos_conflito = AgendamentoModel.query.filter(
        AgendamentoModel.id_profissional == profissional_id,
        AgendamentoModel.status != 'cancelado',
        AgendamentoModel.dt_atendimento < dt_fim
    ).all()
    
    for agendamento in agendamentos_conflito:
        # Calcular fim do agendamento existente
        servico = ServicoModel.query.get(agendamento.id_servico)
        duracao = _obter_duracao_servico(servico)
        ag_fim = agendamento.dt_atendimento + timedelta(minutes=duracao)
        
        # Verificar sobreposição
        if not (dt_fim <= agendamento.dt_atendimento or dt_inicio >= ag_fim):
            return False
    
    return True


def _verificar_disponibilidade_edicao(profissional_id: int, dt_inicio: datetime,
                                     dt_fim: datetime, agendamento_id: int) -> bool:
    """Verifica disponibilidade excluindo o próprio agendamento que está sendo editado"""
    agendamentos_conflito = AgendamentoModel.query.filter(
        AgendamentoModel.id_profissional == profissional_id,
        AgendamentoModel.status != 'cancelado',
        AgendamentoModel.dt_atendimento < dt_fim,
        AgendamentoModel.id != agendamento_id  # Excluir o próprio agendamento
    ).all()
    
    for agendamento in agendamentos_conflito:
        # Calcular fim do agendamento existente
        servico = ServicoModel.query.get(agendamento.id_servico)
        duracao = _obter_duracao_servico(servico)
        ag_fim = agendamento.dt_atendimento + timedelta(minutes=duracao)
        
        # Verificar sobreposição
        if not (dt_fim <= agendamento.dt_atendimento or dt_inicio >= ag_fim):
            return False
    
    return True


def _pode_cancelar_gratuito(agendamento) -> bool:
    """Verifica se o cancelamento pode ser gratuito (mais de 24h de antecedência)"""
    agora = datetime.utcnow()
    diferenca = agendamento.dt_atendimento - agora
    return diferenca.total_seconds() > 24 * 3600  # 24 horas em segundos


def _calcular_taxa_cancelamento(valor_servico: float) -> float:
    """Calcula taxa de cancelamento (20% do valor do serviço)"""
    return valor_servico * 0.20