# services/despesa_service.py
from repositories.despesa_repository import DespesaRepository
from utils.validacoes import validar_despesa
from utils.message_handler import message_handler, MessageType
from utils.logger import logger
from datetime import date

class DespesaService:
    def __init__(self):
        self.repository = DespesaRepository()
    
    def criar_despesa(self, dados_despesa: dict):
        """Cria uma nova despesa com validações"""
        try:
            # Valida os dados da despesa
            validar_despesa(dados_despesa)
            
            # Cria a despesa
            despesa = self.repository.criar(dados_despesa)
            
            message_handler.add_message(
                MessageType.SUCCESS,
                f"Despesa '{despesa.descricao}' cadastrada com sucesso!"
            )
            
            return despesa
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro no serviço de criação de despesa: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao criar despesa. Tente novamente."
            )
            raise
    
    def listar_despesas(self):
        """Lista todas as despesas com relacionamentos"""
        try:
            despesas = self.repository.listar()
            logger.info(f"Listadas {len(despesas)} despesas")
            return despesas
        except Exception as e:
            logger.error(f"Erro ao listar despesas: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao carregar lista de despesas."
            )
            raise
    
    def listar_despesas_pendentes(self):
        """Lista despesas não pagas com relacionamentos"""
        try:
            despesas = self.repository.listar_pendentes()
            logger.info(f"Listadas {len(despesas)} despesas pendentes")
            return despesas
        except Exception as e:
            logger.error(f"Erro ao listar despesas pendentes: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao carregar despesas pendentes."
            )
            raise
    
    def buscar_despesa_por_id(self, despesa_id: int):
        """Busca despesa por ID com relacionamentos"""
        try:
            despesa = self.repository.buscar_por_id(despesa_id)
            if not despesa:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Despesa não encontrada."
                )
            return despesa
        except Exception as e:
            logger.error(f"Erro ao buscar despesa: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao buscar despesa."
            )
            raise
    
    def marcar_despesa_como_paga(self, despesa_id: int, data_pagamento=None):
        """Marca uma despesa como paga"""
        try:
            if not data_pagamento:
                data_pagamento = date.today()
            
            despesa = self.repository.marcar_como_paga(despesa_id, data_pagamento)
            
            if despesa:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    f"Despesa '{despesa.descricao}' marcada como paga!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Despesa não encontrada."
                )
            
            return despesa
        except Exception as e:
            logger.error(f"Erro ao marcar despesa como paga: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao atualizar status da despesa."
            )
            raise
    
    def atualizar_despesa(self, despesa_id: int, dados_atualizacao: dict):
        """Atualiza uma despesa existente"""
        try:
            # Valida os dados de atualização
            validar_despesa(dados_atualizacao, atualizacao=True)
            
            despesa = self.repository.atualizar(despesa_id, dados_atualizacao)
            
            if despesa:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    "Despesa atualizada com sucesso!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Despesa não encontrada para atualização."
                )
            
            return despesa
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar despesa: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao atualizar despesa."
            )
            raise
    
    def deletar_despesa(self, despesa_id: int):
        """Remove uma despesa"""
        try:
            sucesso = self.repository.deletar(despesa_id)
            
            if sucesso:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    "Despesa removida com sucesso!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Despesa não encontrada para remoção."
                )
            
            return sucesso
        except Exception as e:
            logger.error(f"Erro ao deletar despesa: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao remover despesa."
            )
            raise