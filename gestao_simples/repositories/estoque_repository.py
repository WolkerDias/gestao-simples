# repositories/estoque_repository.py
from repositories.base_repository import BaseRepository
from config.database import SessionLocal
from models.estoque import Estoque

class EstoqueRepository(BaseRepository):
    def __init__(self):
        super().__init__(EstoqueRepository)
        
    def criar(self, estoque):
        with SessionLocal() as session:
            session.add(estoque)
            session.commit()
            session.refresh(estoque)
            return estoque
    
    def atualizar(self, estoque_id, nova_quantidade):
        with SessionLocal() as session:
            estoque = session.query(Estoque).filter(Estoque.id == estoque_id).first()
            if estoque:
                estoque.quantidade = nova_quantidade
                session.commit()
                return estoque
            return None
    
    def buscar_por_produto(self, produto_id):
        with SessionLocal() as session:
            return session.query(Estoque).filter(Estoque.produto_id == produto_id).all()
