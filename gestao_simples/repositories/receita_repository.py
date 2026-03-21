# repositories/receita_repository.py
from models.receita import Receita
from sqlalchemy.orm import joinedload
from config.database import SessionLocal
from repositories.base_repository import BaseRepository
from utils.logger import logger

class ReceitaRepository(BaseRepository):
    def __init__(self):
        super().__init__(Receita)
    
    def criar(self, dados_receita: dict) -> Receita:
        """Cria uma nova receita no banco de dados"""
        try:
            nova_receita = Receita(**dados_receita)
            receita_criada = super().criar(nova_receita)
            logger.info(f"Receita criada com sucesso: ID {receita_criada.id}")
            return receita_criada
        except Exception as e:
            logger.error(f"Erro ao criar receita: {str(e)}")
            raise
    
    def atualizar(self, receita_id: int, dados_atualizacao: dict) -> Receita:
        """Atualiza uma receita existente"""
        try:
            receita = self.buscar_por_id(receita_id)
            if not receita:
                return None
            
            for campo, valor in dados_atualizacao.items():
                setattr(receita, campo, valor)
            
            receita_atualizada = super().atualizar(receita)
            logger.info(f"Receita atualizada com sucesso: ID {receita_id}")
            return receita_atualizada
        except Exception as e:
            logger.error(f"Erro ao atualizar receita: {str(e)}")
            raise
    
    def deletar(self, receita_id: int) -> bool:
        """Remove uma receita do banco de dados"""
        try:
            receita = self.buscar_por_id(receita_id)
            if not receita:
                return False
            
            super().deletar(receita_id)
            logger.info(f"Receita deletada com sucesso: ID {receita_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar receita: {str(e)}")
            raise

    def listar_receitas(self):
        """Lista todas as receitas com seus relacionamentos"""
        try:
            with SessionLocal() as session:
                return session.query(Receita)\
                    .options(
                        joinedload(Receita.categoria),
                        joinedload(Receita.conta)
                    )\
                    .all()
        except Exception as e:
            logger.error(f"Erro ao listar receitas: {str(e)}")
            raise
    
    def buscar_receita_por_id(self, receita_id: int):
        """Busca receita por ID com relacionamentos"""
        try:
            with SessionLocal() as session:
                return session.query(Receita)\
                    .options(
                        joinedload(Receita.categoria),
                        joinedload(Receita.conta)
                    )\
                    .filter(Receita.id == receita_id)\
                    .first()
        except Exception as e:
            logger.error(f"Erro ao buscar receita por ID: {str(e)}")
            raise        