# services/produto_service.py
from repositories.produto_repository import ProdutoRepository
from utils.validacoes import validar_produto
from utils.message_handler import message_handler, MessageType
from utils.logger import logger

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
    
    def buscar_produto_por_nome(self, nome):
        try:
            produto = self.repository.buscar_produto_por_nome(nome)
            if produto:
                logger.info(f"Produto encontrado - nome: {produto.nome}")

            else:
                logger.warning(f"Produto não encontrado - nome: {nome}")
            return produto
        except Exception as e:
            error_msg = f"Erro ao buscar produto com nome: {nome}"
            logger.error(f"{error_msg}: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                error_msg
            )
            raise Exception(error_msg) from e    