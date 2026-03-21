# models/categoria_despesa.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class CategoriaDespesa(BaseModel):
    __tablename__ = 'categorias_despesa'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(String(255))
    
    despesas = relationship('Despesa', back_populates='categoria')