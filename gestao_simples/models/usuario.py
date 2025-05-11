# models/usuario.py
from sqlalchemy import Column, Integer, String, Boolean
from pwdlib import PasswordHash
from .base import BaseModel

_pwd_hash = PasswordHash.recommended()

class Usuario(BaseModel):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)

    @property
    def senha(self):
        raise AttributeError('Senha não é acessível')

    @senha.setter
    def senha(self, senha):
        self.senha_hash = _pwd_hash.hash(senha)

    def verificar_senha(self, senha):
        return _pwd_hash.verify(senha, self.senha_hash)