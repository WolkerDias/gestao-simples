# repositories/despesa_repository.py
from sqlalchemy import exists
from config.database import SessionLocal
from sqlalchemy.orm import joinedload
from models.despesa import Despesa
from repositories.base_repository import BaseRepository
from utils.logger import logger

class DespesaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Despesa)
    
    def criar(self, dados_despesa: dict) -> Despesa:
        """Cria uma nova despesa no banco de dados"""
        try:
            with SessionLocal() as session:
                nova_despesa = Despesa(**dados_despesa)
                session.add(nova_despesa)
                session.commit()
                session.refresh(nova_despesa)
                logger.info(f"Despesa criada com sucesso: ID {nova_despesa.id}")
                return nova_despesa
        except Exception as e:
            logger.error(f"Erro ao criar despesa: {str(e)}")
            raise

    def deletar(self, despesa_id: int) -> bool:
        """Remove uma despesa do banco de dados"""
        try:
            with SessionLocal() as session:
                despesa = session.query(Despesa)\
                    .filter(Despesa.id == despesa_id)\
                    .first()
                    
                if not despesa:
                    return False
                
                session.delete(despesa)
                session.commit()
                logger.info(f"Despesa deletada com sucesso: ID {despesa_id}")
                return True
        except Exception as e:
            logger.error(f"Erro ao deletar despesa: {str(e)}")
            raise
    
    def listar(self) -> list[Despesa]:
        """Lista todas as despesas com relacionamentos"""
        try:
            with SessionLocal() as session:
                despesas = session.query(Despesa)\
                    .options(
                        joinedload(Despesa.categoria),
                        joinedload(Despesa.conta)
                    )\
                    .all()
                logger.info(f"Listadas {len(despesas)} despesas")
                return despesas
        except Exception as e:
            logger.error(f"Erro ao listar despesas: {str(e)}")
            raise
    
    def listar_pendentes(self) -> list[Despesa]:
        """Lista despesas não pagas com relacionamentos"""
        try:
            with SessionLocal() as session:
                despesas = session.query(Despesa)\
                    .options(
                        joinedload(Despesa.categoria),
                        joinedload(Despesa.conta)
                    )\
                    .filter(Despesa.paga == False)\
                    .all()
                logger.info(f"Listadas {len(despesas)} despesas pendentes")
                return despesas
        except Exception as e:
            logger.error(f"Erro ao listar despesas pendentes: {str(e)}")
            raise
    
    def buscar_por_id(self, despesa_id: int) -> Despesa:
        """Busca despesa por ID com relacionamentos"""
        try:
            with SessionLocal() as session:
                return session.query(Despesa)\
                    .options(
                        joinedload(Despesa.categoria),
                        joinedload(Despesa.conta)
                    )\
                    .filter(Despesa.id == despesa_id)\
                    .first()
        except Exception as e:
            logger.error(f"Erro ao buscar despesa por ID: {str(e)}")
            raise
    
    def marcar_como_paga(self, despesa_id: int, data_pagamento) -> Despesa:
        """Marca uma despesa como paga e define a data de pagamento"""
        try:
            with SessionLocal() as session:
                # Busca a despesa dentro da mesma sessão
                despesa = session.query(Despesa)\
                    .filter(Despesa.id == despesa_id)\
                    .first()
                    
                if not despesa:
                    return None
                
                # Atualiza os atributos
                despesa.paga = True
                despesa.data_pagamento = data_pagamento
                
                # Faz o commit da transação
                session.commit()
                
                # Recarrega o objeto para garantir que está atualizado
                session.refresh(despesa)
                
                logger.info(f"Despesa marcada como paga: ID {despesa_id}")
                return despesa
        except Exception as e:
            logger.error(f"Erro ao marcar despesa como paga: {str(e)}")
            raise
    
    def atualizar(self, despesa_id: int, dados_atualizacao: dict) -> Despesa:
        """Atualiza uma despesa existente"""
        try:
            with SessionLocal() as session:
                # Busca a despesa dentro da mesma sessão
                despesa = session.query(Despesa)\
                    .filter(Despesa.id == despesa_id)\
                    .first()
                    
                if not despesa:
                    return None
                
                # Atualiza os atributos
                for campo, valor in dados_atualizacao.items():
                    setattr(despesa, campo, valor)
                
                # Faz o commit da transação
                session.commit()
                
                # Recarrega o objeto para garantir que está atualizado
                session.refresh(despesa)
                
                logger.info(f"Despesa atualizada com sucesso: ID {despesa_id}")
                return despesa
        except Exception as e:
            logger.error(f"Erro ao atualizar despesa: {str(e)}")
            raise
    
    def listar_por_categoria(self, categoria_id: int) -> list[Despesa]:
        """Lista despesas por categoria específica"""
        try:
            with SessionLocal() as session:
                despesas = session.query(Despesa).filter(Despesa.categoria_id == categoria_id).all()
                logger.info(f"Listadas {len(despesas)} despesas da categoria {categoria_id}")
                return despesas
        except Exception as e:
            logger.error(f"Erro ao listar despesas por categoria: {str(e)}")
            raise
    
    def verificar_relacionamento_categoria(self, categoria_id: int) -> bool:
        """Verifica se existe despesa vinculada à categoria"""
        return super().existe_relacionamento(Despesa.categoria_id, categoria_id)
