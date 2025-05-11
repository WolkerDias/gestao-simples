# services/fornecedor_service.py
from repositories.fornecedor_repository import FornecedorRepository
from utils.validacoes import validar_fornecedor, ValidationError
from utils.message_handler import message_handler, MessageType
from utils.logger import logger
from models.nota_entrada import NotaEntrada

class FornecedorService:
    def __init__(self):
        self.repository = FornecedorRepository()
    
    def criar_fornecedor(self, dados):
        try:
            validar_fornecedor(dados)
            fornecedor = self.repository.criar(dados)
            logger.info(f"Fornecedor {fornecedor.nome} criado com sucesso")
            return fornecedor
        except ValidationError as e:
            logger.error(f"Erro de validação ao criar fornecedor: {e.errors}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar fornecedor: {str(e)}")
            raise Exception(f"Erro ao criar fornecedor: {str(e)}")
    
    def listar_fornecedores(self):
        try:
            fornecedores = self.repository.listar()
            logger.info(f"Listados {len(fornecedores)} fornecedores")
            return fornecedores
        except Exception as e:
            error_msg = "Erro ao listar fornecedores"
            logger.error(f"{error_msg}: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                error_msg
            )
            raise Exception(error_msg) from e
    
    def buscar_fornecedor_por_id(self, id):
        try:
            fornecedor = self.repository.buscar_por_id(id)
            if fornecedor:
                logger.info(f"Fornecedor encontrado - ID: {id}, Nome: {fornecedor.nome}")

            else:
                logger.warning(f"Fornecedor não encontrado - ID: {id}")
                message_handler.add_message(
                    MessageType.WARNING,
                    f"Fornecedor com ID {id} não encontrado"
                )
            return fornecedor
        except Exception as e:
            error_msg = f"Erro ao buscar fornecedor com ID {id}"
            logger.error(f"{error_msg}: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                error_msg
            )
            raise Exception(error_msg) from e
    
    def buscar_fornecedor_por_cnpj(self, cnpj):
        try:
            fornecedor = self.repository.buscar_fornecedor_por_cnpj(cnpj)
            if fornecedor:
                logger.info(f"Fornecedor encontrado - CNPJ: {cnpj}, Nome: {fornecedor.nome}")

            else:
                logger.warning(f"Fornecedor não encontrado - CNPJ: {cnpj}")
            return fornecedor
        except Exception as e:
            error_msg = f"Erro ao buscar fornecedor com CNPJ: {cnpj}"
            logger.error(f"{error_msg}: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                error_msg
            )
            raise Exception(error_msg) from e
    
    def atualizar_fornecedor(self, dados):
        try:
            validar_fornecedor(dados)
            fornecedor = self.repository.atualizar(dados)
            logger.info(f"Fornecedor {fornecedor.nome} atualizado com sucesso")
            message_handler.add_message(
                MessageType.SUCCESS,
                f"Fornecedor {fornecedor.nome} atualizado com sucesso!"
            )
            return fornecedor
        except ValidationError as e:
            error_msg = "Erro de validação ao atualizar fornecedor"
            logger.error(f"{error_msg}: {e.errors}")
            message_handler.add_message(
                MessageType.ERROR,
                error_msg
            )
            raise
        except Exception as e:
            error_msg = "Erro inesperado ao atualizar fornecedor"
            logger.error(f"{error_msg}: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                error_msg
            )
            raise Exception(error_msg) from e
    
    def deletar_fornecedor(self, id):
        try:
            # Primeiro busca o fornecedor para ter informações para o log
            fornecedor = self.repository.buscar_por_id(id)
            if not fornecedor:
                error_msg = f"Fornecedor com ID {id} não encontrado para deletar"
                logger.warning(error_msg)
                message_handler.add_message(
                    MessageType.WARNING,
                    error_msg
                )
                return

            # Verifica se existem registros associados
            if self.repository.existe_relacionamento(NotaEntrada.fornecedor_id, id):
                error_msg = f"Não é possível excluir o fornecedor {fornecedor.nome} (ID {id}) pois existe NotaEntrada associada."
                logger.warning(error_msg)
                message_handler.add_message(MessageType.WARNING, error_msg)
                return            
            
            # Se encontrou, tenta deletar
            nome_fornecedor = fornecedor.nome  # Guarda o nome para usar na mensagem
            self.repository.deletar(id)
            
            success_msg = f"Fornecedor {nome_fornecedor} deletado com sucesso!"
            logger.info(success_msg)
            message_handler.add_message(
                MessageType.SUCCESS,
                success_msg
            )
        except Exception as e:
            error_msg = f"Erro ao deletar fornecedor com ID {id}"
            logger.error(f"{error_msg}: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                error_msg
            )
            raise Exception(f"{error_msg}: {str(e)}") from e