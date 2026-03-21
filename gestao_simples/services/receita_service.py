# services/receita_service.py
from repositories.receita_repository import ReceitaRepository
from utils.validacoes import validar_receita
from utils.message_handler import message_handler, MessageType
from utils.logger import logger
from datetime import date

class ReceitaService:
    def __init__(self):
        self.repository = ReceitaRepository()
    
    def criar_receita(self, dados_receita: dict):
        """Cria uma nova receita com validações"""
        try:
            # Valida os dados da receita
            validar_receita(dados_receita)
            
            # Cria a receita
            receita = self.repository.criar(dados_receita)
            
            message_handler.add_message(
                MessageType.SUCCESS,
                f"Receita '{receita.descricao}' cadastrada com sucesso!"
            )
            
            return receita
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro no serviço de criação de receita: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao criar receita. Tente novamente."
            )
            raise
    
    def listar_receitas(self):
        """Lista todas as receitas com relacionamentos"""
        try:
            receitas = self.repository.listar_receitas()
            logger.info(f"Listadas {len(receitas)} receitas")
            return receitas
        except Exception as e:
            logger.error(f"Erro ao listar receitas: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao carregar lista de receitas."
            )
            raise
    
    def buscar_receita_por_id(self, receita_id: int):
        """Busca receita por ID com relacionamentos"""
        try:
            receita = self.repository.buscar_receita_por_id(receita_id)
            if not receita:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Receita não encontrada."
                )
            return receita
        except Exception as e:
            logger.error(f"Erro ao buscar receita: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro ao buscar receita."
            )
            raise
    
    def atualizar_receita(self, receita_id: int, dados_atualizacao: dict):
        """Atualiza uma receita existente"""
        try:
            # Valida os dados de atualização
            validar_receita(dados_atualizacao, atualizacao=True)
            
            receita = self.repository.atualizar(receita_id, dados_atualizacao)
            
            if receita:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    "Receita atualizada com sucesso!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Receita não encontrada para atualização."
                )
            
            return receita
        except ValueError as e:
            message_handler.add_message(MessageType.ERROR, str(e))
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar receita: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao atualizar receita."
            )
            raise
    
    def deletar_receita(self, receita_id: int):
        """Remove uma receita"""
        try:
            sucesso = self.repository.deletar(receita_id)
            
            if sucesso:
                message_handler.add_message(
                    MessageType.SUCCESS,
                    "Receita removida com sucesso!"
                )
            else:
                message_handler.add_message(
                    MessageType.WARNING,
                    "Receita não encontrada para remoção."
                )
            
            return sucesso
        except Exception as e:
            logger.error(f"Erro ao deletar receita: {str(e)}")
            message_handler.add_message(
                MessageType.ERROR,
                "Erro interno ao remover receita."
            )
            raise