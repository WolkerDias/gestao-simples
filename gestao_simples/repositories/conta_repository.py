# repositories/conta_repository.py
from models.conta import Conta
from repositories.base_repository import BaseRepository
from config.database import SessionLocal
from utils.logger import logger

class ContaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Conta)
    
    def criar(self, dados_conta: dict) -> Conta:
        """Cria uma nova conta no banco de dados"""
        try:
            nova_conta = Conta(**dados_conta)
            conta_criada = super().criar(nova_conta)
            logger.info(f"Conta criada com sucesso: ID {conta_criada.id}")
            return conta_criada
        except Exception as e:
            logger.error(f"Erro ao criar conta: {str(e)}")
            raise
    
    def atualizar(self, conta_id: int, dados_atualizacao: dict) -> Conta:
        """Atualiza uma conta existente"""
        try:
            conta = self.buscar_por_id(conta_id)
            if not conta:
                return None
            
            for campo, valor in dados_atualizacao.items():
                setattr(conta, campo, valor)
            
            conta_atualizada = super().atualizar(conta)
            logger.info(f"Conta atualizada com sucesso: ID {conta_id}")
            return conta_atualizada
        except Exception as e:
            logger.error(f"Erro ao atualizar conta: {str(e)}")
            raise
    
    def deletar(self, conta_id: int) -> bool:
        """Remove uma conta do banco de dados"""
        try:
            conta = self.buscar_por_id(conta_id)
            if not conta:
                return False
            
            super().deletar(conta_id)
            logger.info(f"Conta deletada com sucesso: ID {conta_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar conta: {str(e)}")
            raise
    
    def buscar_por_nome(self, nome: str) -> Conta:
        """Busca conta por nome"""
        try:
            with SessionLocal() as session:
                # Utiliza ilike para busca case-insensitive
                return session.query(Conta).filter(
                    Conta.nome.ilike(f"%{nome}%")
                ).first()
        except Exception as e:
            logger.error(f"Erro ao buscar conta por nome: {str(e)}")
            raise
    
    def listar_por_tipo(self, tipo: str):
        """Lista contas por tipo"""
        try:
            with SessionLocal() as session:
                # Filtra contas pelo tipo especificado
                return session.query(Conta).filter(Conta.tipo == tipo).all()
        except Exception as e:
            logger.error(f"Erro ao listar contas por tipo: {str(e)}")
            raise
    
    def calcular_saldo_atual(self, conta_id: int) -> float:
        """Calcula o saldo atual da conta baseado nas receitas e despesas"""
        try:
            conta = self.buscar_por_id(conta_id)
            if not conta:
                return 0.0
            
            # Saldo inicial
            saldo_atual = float(conta.saldo_inicial or 0.0)
            
            # Soma receitas
            for receita in conta.receitas:
                saldo_atual += float(receita.valor)
            
            # Subtrai despesas
            for despesa in conta.despesas:
                saldo_atual -= float(despesa.valor)
            
            return saldo_atual
        except Exception as e:
            logger.error(f"Erro ao calcular saldo da conta: {str(e)}")
            raise