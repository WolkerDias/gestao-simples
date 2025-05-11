# models/produto.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import BaseModel

class Produto(BaseModel):
    __tablename__ = 'produtos'
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255))
    unidade_medida = Column(String(2), nullable=False)

    associacoes_fornecedores = relationship('ProdutoFornecedorAssociacao', back_populates='produto')
    itens_inventario = relationship('ItemInventario', back_populates='produto')