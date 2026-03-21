# repositories/categoria_despesa_repository.py
from sqlalchemy import exists
from config.database import SessionLocal
from models.categoria_despesa import CategoriaDespesa
from repositories.base_repository import BaseRepository
from utils.logger import logger

class CategoriaDespesaRepository(BaseRepository):
    def __init__(self):
        super().__init__(CategoriaDespesa)
    
    def criar(self, dados_categoria: dict) -> CategoriaDespesa:
        """Cria uma nova categoria de despesa no banco de dados"""
        try:
            nova_categoria = CategoriaDespesa(**dados_categoria)
            categoria_criada = super().criar(nova_categoria)
            logger.info(f"Categoria de despesa criada com sucesso: ID {categoria_criada.id}")
            return categoria_criada
        except Exception as e:
            logger.error(f"Erro ao criar categoria de despesa: {str(e)}")
            raise
    
    def atualizar(self, categoria_id: int, dados_atualizacao: dict) -> CategoriaDespesa:
        """Atualiza uma categoria de despesa existente"""
        try:
            categoria = self.buscar_por_id(categoria_id)
            if not categoria:
                return None
            
            for campo, valor in dados_atualizacao.items():
                setattr(categoria, campo, valor)
            
            categoria_atualizada = super().atualizar(categoria)
            logger.info(f"Categoria de despesa atualizada com sucesso: ID {categoria_id}")
            return categoria_atualizada
        except Exception as e:
            logger.error(f"Erro ao atualizar categoria de despesa: {str(e)}")
            raise
    
    def deletar(self, categoria_id: int) -> bool:
        """Remove uma categoria de despesa do banco de dados"""
        try:
            categoria = self.buscar_por_id(categoria_id)
            if not categoria:
                return False
            
            super().deletar(categoria_id)
            logger.info(f"Categoria de despesa deletada com sucesso: ID {categoria_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar categoria de despesa: {str(e)}")
            raise
    
    def buscar_por_nome(self, nome: str) -> CategoriaDespesa:
        """Busca categoria de despesa por nome"""
        try:
            with SessionLocal() as session:
                return session.query(CategoriaDespesa).filter(
                    CategoriaDespesa.nome.ilike(f"%{nome}%")
                ).first()
        except Exception as e:
            logger.error(f"Erro ao buscar categoria por nome: {str(e)}")
            raise
    
    def verificar_relacionamento_despesa(self, categoria_id: int) -> bool:
        """Verifica se existe despesa vinculada à categoria"""
        try:
            from models.despesa import Despesa
            return super().existe_relacionamento(Despesa.categoria_id, categoria_id)
        except Exception as e:
            logger.error(f"Erro ao verificar relacionamento com despesas: {str(e)}")
            raise
    
    def listar_categorias_com_despesas(self) -> list[CategoriaDespesa]:
        """Lista categorias que possuem despesas vinculadas"""
        try:
            with SessionLocal() as session:
                from models.despesa import Despesa
                categorias = session.query(CategoriaDespesa).join(
                    Despesa, CategoriaDespesa.id == Despesa.categoria_id
                ).distinct().all()
                logger.info(f"Listadas {len(categorias)} categorias com despesas")
                return categorias
        except Exception as e:
            logger.error(f"Erro ao listar categorias com despesas: {str(e)}")
            raise
    
    def contar_despesas_por_categoria(self, categoria_id: int) -> int:
        """Conta quantas despesas estão vinculadas à categoria"""
        try:
            with SessionLocal() as session:
                from models.despesa import Despesa
                count = session.query(Despesa).filter(
                    Despesa.categoria_id == categoria_id
                ).count()
                return count
        except Exception as e:
            logger.error(f"Erro ao contar despesas da categoria: {str(e)}")
            raise