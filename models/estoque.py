# models/estoque.py
from sqlalchemy import Column, Integer, Float, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from models.base import BaseModel

class Estoque(BaseModel):
    __tablename__ = 'estoques'
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey('produtos.id'))
    quantidade = Column(Float, default=0)
    
    produto = relationship("Produto", back_populates="estoques")