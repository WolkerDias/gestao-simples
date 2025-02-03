# repositories/produto_repository.py
from repositories.base_repository import BaseRepository
from models.produto import Produto

class ProdutoRepository(BaseRepository):
    def __init__(self):
        super().__init__(Produto)