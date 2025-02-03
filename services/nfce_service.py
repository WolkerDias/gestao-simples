# services/nfce_service.py
from repositories.nfce_repository import NFCeRepository
from utils.validacoes import validar_fornecedor, ValidationError
from utils.logger import logger
from utils.message_handler import message_handler, MessageType



class NFCeService:
    def __init__(self):
        self.repository = NFCeRepository()
    
    def criar_nfce(self, dados):
        try:
            nfce = self.repository.criar(dados)
            success_msg = f"NFCe cadastrado com sucesso"
            logger.info(success_msg)
            message_handler.add_message(
                MessageType.SUCCESS,
                success_msg
            )
            return nfce
        except ValidationError as e:
            logger.error(f"Erro de validação ao criar NFCe: {e.errors}")
            raise
        except Exception as e:
            logger.error(f"Erro ao criar NFCe: {str(e)}")
            raise Exception(f"Erro ao criar NFCe: {str(e)}")
        
    def listar_nfces(self):
        return self.repository.listar()
    
    def buscar_nfce_por_id(self, id):
        return self.repository.buscar_por_id(id)
    
    def atualizar_nfce(self, dados):
        return self.repository.atualizar(dados)
    
    def deletar_nfce(self, id):
        return self.repository.deletar(id)