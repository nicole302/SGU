class Usuario:
    # comstrutor da classe
    def __init__(self, nome, email, telefone, senha):
        self.__nome = nome
        self.__email = email
        self.__telefone = telefone
        self.__senha = senha
        
    # get e set para manipular os atributos
    @property
    def nome(self):
        return self.__nome
    
    @nome.setter
    def nome(self, nome):
        self.__nome = nome
        
    @property
    def email(self):
        return self.__email
    
    @email.setter
    def email(self, email):        
        self.__email = email
        
    @property
    def telefone(self):
        return self.__telefone
    
    @telefone.setter
    def telefone(self, telefone):
        self.__telefone = telefone
        
    @property
    def senha(self):
        return self.__senha
    
    @senha.setter
    def senha(self, senha):
        self.__senha = senha
             
        
         