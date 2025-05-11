# repositories/item_nota_entrada_repository.py
from repositories.base_repository import BaseRepository
from models.item_nota_entrada import ItemNotaEntrada
from config.database import SessionLocal

class ItemNotaEntradaRepository(BaseRepository):
    def __init__(self):
        super().__init__(ItemNotaEntrada)
    
    def listar_por_nota_entrada(self, nota_entrada_id, session=None):
        if session is None:
            session = SessionLocal()
        with session:
            return session.query(self.model).filter(self.model.nota_entrada_id == nota_entrada_id).all()
    
    def criar(self, obj, session=None):
        if session is None:
            session = SessionLocal()
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj
    
    def atualizar(self, obj, session=None):
        if session is None:
            session = SessionLocal()
        # Não use with session: (remove essa linha)
        session.merge(obj)
        # Não faça commit aqui! ❌
        return obj

    def deletar(self, id, session=None):
        try:
            if session:
                item = session.query(self.model).get(id)
                if item:
                    session.delete(item)
                    # Não faça commit aqui! ❌
            else:
                super().deletar(id)
        except Exception as e:
            raise
        
    def buscar_por_id(self, id, session=None):
        if session is None:
            session = SessionLocal()        
        with session:
            return session.query(self.model).filter(self.model.id == id).first()