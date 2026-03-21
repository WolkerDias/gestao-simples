# models/conta.py
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
from .base import BaseModel

class Conta(BaseModel):
    __tablename__ = 'contas'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True)
    tipo = Column(String(50), nullable=False)  # banco, carteira, poupanca, etc
    saldo_inicial = Column(Numeric(10, 2), default=0.00)
    
    receitas = relationship('Receita', back_populates='conta')
    despesas = relationship('Despesa', back_populates='conta')