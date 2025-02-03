# repositories/produto_repository.py
from repositories.base_repository import BaseRepository
from models.item_nfce import ItemNFCe
from config.database import SessionLocal

class ItemNFCeRepository(BaseRepository):
    def __init__(self):
        super().__init__(ItemNFCe)
    
    def listar_por_nfce(self, nfce_id):
        with SessionLocal() as session:
            return session.query(self.model).filter(self.model.nfce_id == nfce_id).all()