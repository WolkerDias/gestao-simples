# models/nota_entrada.py
from sqlalchemy import Column, String, ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import relationship
from models.base import BaseModel

class NotaEntrada(BaseModel):
    __tablename__ = 'notas_entrada' 

    id = Column(Integer, primary_key=True, autoincrement=True)
    modelo = Column(Integer, nullable=True)
    chave_acesso = Column(String(44), unique=True, nullable=True)
    fornecedor_id = Column(Integer, ForeignKey('fornecedores.id'))
    data_emissao = Column(DateTime, nullable=False)
    url = Column(String(255), nullable=True)
    numero_nota_entrada = Column(Integer, nullable=True)
    serie_nota_entrada = Column(Integer, nullable=True)
    total_nota_entrada = Column(Float, nullable=False)
    
    itens = relationship('ItemNotaEntrada', backref='notas_entrada', cascade='all, delete-orphan')