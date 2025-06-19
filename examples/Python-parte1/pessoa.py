
class Pessoa:
        def __init__(self, nome, cidade, telefone, ano):
            self.nome = nome
            self.cidade = cidade
            self.telefone = telefone
            self.ano = ano

        def toString(self):
            return self.nome+', '+self.cidade+', '+self.telefone+', '+self.ano


