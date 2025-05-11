# models/produto_fornecedor_associacao.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class ProdutoFornecedorAssociacao(BaseModel):
    __tablename__ = 'produto_fornecedor_associacao'

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    fornecedor_id = Column(Integer, ForeignKey('fornecedores.id'), nullable=False)
    quantidade_por_grade = Column(Float, nullable=False)
    codigo_produto_fornecedor = Column(String(255), nullable=False)
    descricao_produto_fornecedor = Column(String(255), nullable=False)

    produto = relationship('Produto', back_populates='associacoes_fornecedores')
    fornecedor = relationship('Fornecedor', back_populates='associacoes_produtos')