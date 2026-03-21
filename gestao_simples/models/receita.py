# models/receita.py
from sqlalchemy import Column, Integer, String, Numeric, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Receita(BaseModel):
    __tablename__ = 'receitas'
    
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(200), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    data_recebimento = Column(Date, nullable=False)
    categoria_id = Column(Integer, ForeignKey('categorias_receita.id'), nullable=False)
    observacoes = Column(Text)
    conta_id = Column(Integer, ForeignKey('contas.id'), nullable=True)
    
    categoria = relationship('CategoriaReceita', back_populates='receitas')
    conta = relationship('Conta', back_populates='receitas')