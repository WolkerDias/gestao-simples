# models/item_nota_entrada.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from models.base import BaseModel

class ItemNotaEntrada(BaseModel):
    __tablename__ = 'itens_nota_entrada'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_entrada_id = Column(Integer, ForeignKey('notas_entrada.id'))
    codigo_produto_fornecedor = Column(String(255), nullable=True)
    descricao = Column(String(255), nullable=False)
    quantidade = Column(Float, nullable=False)
    unidade_medida = Column(String(50), nullable=False)
    valor = Column(Float, nullable=False)