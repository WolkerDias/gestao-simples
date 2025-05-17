# services/produto_service.py
from repositories.produto_repository import ProdutoRepository
from models.produto_fornecedor_associacao import ProdutoFornecedorAssociacao
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
        try:
            # Primeiro busca o produto para ter informações para o log
            produto = self.repository.buscar_por_id(id)
            if not produto:
                error_msg = f"Produto com ID {id} não encontrado para deletar"
                logger.warning(error_msg)
                message_handler.add_message(
                    MessageType.WARNING,
                    error_msg
                )
                return

            # Verifica se existem registros associados
            if self.repository.existe_relacionamento(ProdutoFornecedorAssociacao.produto_id, id):
                error_msg = f"Não é possível excluir o produto {produto.nome} (ID {id}) pois existe associação relacionada."
                logger.warning(error_msg)
                message_handler.add_message(
                    MessageType.WARNING, 
                    error_msg
                )
                return            
            
            # Se encontrou, tenta deletar
            nome_produto = produto.nome  # Guarda o nome para usar na mensagem
            self.repository.deletar(id)
            
            success_msg = f"Produto {nome_produto} deletado com sucesso!"
            logger.info(success_msg)
            message_handler.add_message(
                MessageType.SUCCESS,
                success_msg
            )
        except Exception as e:
            error_msg = f"Erro ao deletar produto com ID {id}"
            logger.error(f"{error_msg}: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                error_msg
            )
            raise Exception(f"{error_msg}: {str(e)}") from e
    
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