# services/produto_service.py
from repositories.produto_repository import ProdutoRepository
from utils.validacoes import validar_produto

class ProdutoService:
    def __init__(self):
        self.repository = ProdutoRepository()
    
    def criar_produto(self, dados):
        validar_produto(dados)
        return self.repository.criar(dados)
    
    def listar_produtos(self):
        return self.repository.listar()
    
    def buscar_produto_por_id(self, id):
        return self.repository.buscar_por_id(id)
    
    def atualizar_produto(self, dados):
        validar_produto(dados)
        return self.repository.atualizar(dados)
    
    def deletar_produto(self, id):
        return self.repository.deletar(id)