# models/fornecedor.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class Fornecedor(BaseModel):
    __tablename__ = 'fornecedores'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=False)
    email = Column(String(100))
    telefone = Column(String(20))
    
    produtos = relationship("Produto", back_populates="fornecedor")