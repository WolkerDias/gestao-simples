# models/inventario_item.py
from sqlalchemy import Column, Integer, Float, ForeignKey
from models.base import BaseModel
from sqlalchemy.orm import relationship


class ItemInventario(BaseModel):
    __tablename__ = 'itens_inventario'

    id = Column(Integer, primary_key=True, autoincrement=True)
    inventario_id = Column(Integer, ForeignKey('inventario_estoque.id'), nullable=False)
    produto_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    quantidade_contada = Column(Float, nullable=False)

    # Relacionamentos
    inventario = relationship('InventarioEstoque', back_populates='itens')
    produto = relationship('Produto', back_populates='itens_inventario')