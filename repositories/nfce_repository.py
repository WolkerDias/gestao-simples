# repositories/produto_repository.py
from repositories.base_repository import BaseRepository
from models.nfce import NFCe

class NFCeRepository(BaseRepository):
    def __init__(self):
        super().__init__(NFCe)