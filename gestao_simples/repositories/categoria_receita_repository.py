# repositories/categoria_receita_repository.py
from models.categoria_receita import CategoriaReceita
from models.receita import Receita
from repositories.base_repository import BaseRepository
from config.database import SessionLocal
from sqlalchemy.orm import joinedload
from utils.logger import logger

class CategoriaReceitaRepository(BaseRepository):
    def __init__(self):
        super().__init__(CategoriaReceita)
    
    def criar(self, dados_categoria: dict) -> CategoriaReceita:
        """Cria uma nova categoria de receita no banco de dados"""
        try:
            nova_categoria = CategoriaReceita(**dados_categoria)
            categoria_criada = super().criar(nova_categoria)
            logger.info(f"Categoria de receita criada com sucesso: ID {categoria_criada.id}")
            return categoria_criada
        except Exception as e:
            logger.error(f"Erro ao criar categoria de receita: {str(e)}")
            raise
    
    def atualizar(self, categoria_id: int, dados_atualizacao: dict) -> CategoriaReceita:
        """Atualiza uma categoria de receita existente"""
        try:
            categoria = self.buscar_por_id(categoria_id)
            if not categoria:
                return None
            
            for campo, valor in dados_atualizacao.items():
                setattr(categoria, campo, valor)
            
            categoria_atualizada = super().atualizar(categoria)
            logger.info(f"Categoria de receita atualizada com sucesso: ID {categoria_id}")
            return categoria_atualizada
        except Exception as e:
            logger.error(f"Erro ao atualizar categoria de receita: {str(e)}")
            raise
    
    def deletar(self, categoria_id: int) -> bool:
        """Remove uma categoria de receita do banco de dados"""
        try:
            categoria = self.buscar_por_id(categoria_id)
            if not categoria:
                return False
            
            super().deletar(categoria_id)
            logger.info(f"Categoria de receita deletada com sucesso: ID {categoria_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar categoria de receita: {str(e)}")
            raise
    
    def buscar_por_nome(self, nome: str) -> CategoriaReceita:
        """Busca categoria de receita por nome"""
        try:
            with SessionLocal() as session:
                return session.query(CategoriaReceita).filter(
                    CategoriaReceita.nome.ilike(f"%{nome}%")
                ).first()
        except Exception as e:
            logger.error(f"Erro ao buscar categoria por nome: {str(e)}")
            raise       

    def contar_receitas_por_categoria(self, categoria_id: int) -> int:
        """Conta o número de receitas associadas a uma categoria"""
        try:
            with SessionLocal() as session:
                # Carrega a categoria com o relacionamento receitas
                categoria = session.query(CategoriaReceita)\
                    .options(joinedload(CategoriaReceita.receitas))\
                    .filter(CategoriaReceita.id == categoria_id)\
                    .first()
                
                if not categoria:
                    return 0
                
                return len(categoria.receitas)
        except Exception as e:
            logger.error(f"Erro ao contar receitas por categoria: {str(e)}")
            raise

    def buscar_por_id(self, id: int) -> CategoriaReceita:
        """Busca categoria por ID com relacionamentos carregados"""
        try:
            with SessionLocal() as session:
                return session.query(CategoriaReceita)\
                    .options(joinedload(CategoriaReceita.receitas))\
                    .filter(CategoriaReceita.id == id)\
                    .first()
        except Exception as e:
            logger.error(f"Erro ao buscar categoria por ID: {str(e)}")
            raise

    def listar(self):
        """Lista todas as categorias de receita com seus relacionamentos"""
        try:
            with SessionLocal() as session:
                # Carrega as categorias e o relacionamento receitas
                categorias = session.query(CategoriaReceita)\
                    .options(joinedload(CategoriaReceita.receitas))\
                    .all()
                return categorias
        except Exception as e:
            logger.error(f"Erro ao listar categorias: {str(e)}")
            raise             