# models/item_nfce.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from models.base import BaseModel

class ItemNFCe(BaseModel):
    __tablename__ = 'itens_nfce'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nfce_id = Column(Integer, ForeignKey('nfce.id'))
    codigo_produto_fornecedor = Column(Integer, nullable=True)
    produto = Column(String(255), nullable=True)
    descricao = Column(String(255), nullable=False)
    quantidade = Column(Float, nullable=False)
    unidade_medida = Column(String(2), nullable=False)
    quantidade_por_grade = Column(Float, nullable=True)
    valor = Column(Float, nullable=False)