class Servico:
    def __init__(self, descricao: str, valor: float, horario_duracao: float):
        self.__descriçao = descricao
        self.__valor = valor
        self.__horario_duracao = horario_duracao
        
        
    @property
    def descrica(self):
        return self.__descriçao
    
    @property
    def valor(self):
        return self.__valor   
    
    @property
    def horario_duracao(self):
        return self.__horario_duracao
     
    
    
    
    