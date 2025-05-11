# models/inventario_estoque.py
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from models.base import BaseModel

class InventarioEstoque(BaseModel):
    __tablename__ = 'inventario_estoque'

    id = Column(Integer, primary_key=True, autoincrement=True)
    referencia = Column(String(7), nullable=False, unique=True)  # Ex: "04/2025"
    data_inicio_contagem = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    data_fim_contagem = Column(DateTime(timezone=True), nullable=True)
    observacoes = Column(String(255))
    
    # Relacionamento com os itens do inventário
    itens = relationship('ItemInventario', back_populates='inventario', cascade='all, delete-orphan')