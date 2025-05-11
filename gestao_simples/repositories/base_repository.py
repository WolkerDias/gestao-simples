# repositories/base_repository.py
from config.database import SessionLocal
from sqlalchemy import exists

class BaseRepository:
    def __init__(self, model):
        self.model = model
        
    def criar(self, obj):
        with SessionLocal() as session:
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj
    
    def listar(self):
        with SessionLocal() as session:
            return session.query(self.model).all()
    
    def buscar_por_id(self, id):
        with SessionLocal() as session:
            return session.query(self.model).filter(self.model.id == id).first()
    
    def atualizar(self, obj):
        with SessionLocal() as session:
            session.merge(obj)
            session.commit()
            return obj
    
    def deletar(self, id):
        with SessionLocal() as session:
            obj = session.query(self.model).filter(self.model.id == id).first()
            session.delete(obj)
            session.commit()

        
    def existe_relacionamento(self, entidade_id, id: int) -> bool:
        """
        Verifica se há registros vinculados de relacionamento com a entidade.
        Retorna True se houver, False caso contrário.
        """
        with SessionLocal() as session:  # Usa um gerenciador de contexto para a sessão
            existe = session.query(exists().where(entidade_id == id)).scalar()
            return existe