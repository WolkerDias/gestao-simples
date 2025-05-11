# repositories/nota_entrada_repository.py
from repositories.base_repository import BaseRepository
from config.database import SessionLocal
from models.nota_entrada import NotaEntrada

class NotaEntradaRepository(BaseRepository):
    def __init__(self):
        super().__init__(NotaEntrada)

    def criar(self, obj, session=None):
        if session is None:
            session = SessionLocal()
            session.add(obj)
            session.commit()
            session.refresh(obj)
        else:
            session.add(obj)
            session.flush()  # Força o flush para gerar o ID
        return obj
    
    def atualizar(self, obj, session=None):
        if session is None:
            session = SessionLocal()        
        with session:
            session.merge(obj)
            session.commit()
            return obj
        
    def buscar_por_chave_acesso(self, chave_acesso, session=None):
        if session is None:
            session = SessionLocal()        
        with session:        
            return session.query(NotaEntrada).filter(NotaEntrada.chave_acesso == chave_acesso).first()
        
    def listar_por_fornecedor_ordenado(self, fornecedor_id: int, session=None):
        if session is None:
            session = SessionLocal()
        return (
            session.query(NotaEntrada)
            .filter(NotaEntrada.fornecedor_id == fornecedor_id)
            .order_by(NotaEntrada.data_emissao.desc())
            .all()
        )