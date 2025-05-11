# repositories/usuario_repository.py
from models.usuario import Usuario
from repositories.base_repository import BaseRepository
from config.database import SessionLocal

class UsuarioRepository(BaseRepository):
    def __init__(self):
        super().__init__(Usuario)

    def criar(self, usuario: Usuario):
        with SessionLocal() as session:
            session.add(usuario)
            session.commit()
            session.refresh(usuario)
        return usuario

    def buscar_por_email(self, email: str):
        with SessionLocal() as session:
            return session.query(Usuario).filter_by(email=email).first()