# models/categoria_receita.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class CategoriaReceita(BaseModel):
    __tablename__ = 'categorias_receita'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(String(255))
    
    receitas = relationship('Receita', back_populates='categoria')