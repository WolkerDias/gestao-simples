# repositories/produto_repository.py
from repositories.base_repository import BaseRepository
from models.fornecedor import Fornecedor
from config.database import SessionLocal


class FornecedorRepository(BaseRepository):
    def __init__(self):
        super().__init__(Fornecedor)
        
    def buscar_fornecedor_por_cnpj(self, cnpj):
        with SessionLocal() as session:
            return session.query(Fornecedor).filter_by(cnpj=cnpj).first()