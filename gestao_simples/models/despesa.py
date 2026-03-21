# models/despesa.py
from sqlalchemy import Column, Integer, String, Numeric, Date, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class Despesa(BaseModel):
    __tablename__ = 'despesas'
    
    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String(200), nullable=False)
    valor = Column(Numeric(10, 2), nullable=False)
    data_vencimento = Column(Date, nullable=False)
    data_pagamento = Column(Date, nullable=True)
    categoria_id = Column(Integer, ForeignKey('categorias_despesa.id'), nullable=False)
    observacoes = Column(Text)
    conta_id = Column(Integer, ForeignKey('contas.id'), nullable=True)
    paga = Column(Boolean, default=False, nullable=False)
    
    categoria = relationship('CategoriaDespesa', back_populates='despesas')
    conta = relationship('Conta', back_populates='despesas')