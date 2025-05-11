# services/estoque_service.py
from repositories.estoque_repository import EstoqueRepository
from models.estoque import Estoque

class EstoqueService:
    def __init__(self):
        self.repository = EstoqueRepository()
    
    def criar_estoque(self, produto_id, quantidade=0, referencia=None, data_conferencia=None):
        novo_estoque = Estoque(
            produto_id=produto_id, 
            quantidade=quantidade,
            referencia=referencia,
            data_conferencia=data_conferencia
        )
        return self.repository.criar(novo_estoque)
    
    def listar_estoques(self):
        return self.repository.listar()
    
    def atualizar_quantidade(self, estoque_id, nova_quantidade):
        return self.repository.atualizar(estoque_id, nova_quantidade)
    
    def obter_estoque_produto(self, produto_id):
        return self.repository.buscar_por_produto(produto_id)