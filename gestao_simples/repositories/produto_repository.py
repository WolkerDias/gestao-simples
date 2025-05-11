# repositories/produto_repository.py
from repositories.base_repository import BaseRepository
from models.produto import Produto
from config.database import SessionLocal

class ProdutoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Produto)

    def buscar_produto_por_nome(self, nome):
        with SessionLocal() as session:
            return session.query(Produto).filter_by(nome=nome).first()        